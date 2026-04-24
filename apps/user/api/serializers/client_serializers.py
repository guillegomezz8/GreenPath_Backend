from rest_framework import serializers
from django.db.models import Sum, Max, Count, Q
import logging

from apps.base.logger import configure_logging
from apps.user.models.client import Client
from apps.user.models.user import User
from apps.user.utils import is_auto_generated_client_email, sync_client_location_from_address
from apps.collection.models import Collection
from apps.base.enums import PickupFrequency, CollectionStatus

configure_logging()


class ClientSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", read_only=True)
    frequency = serializers.SerializerMethodField()
    total_pick_ups = serializers.SerializerMethodField()
    last_pick_up = serializers.SerializerMethodField()
    last_completed_pick_up = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Client
        exclude = ("modified_date", "deleted_date", "created_date")

    def _get_collection_stats(self, obj):
        if hasattr(obj, "_collection_stats_cache"):
            return obj._collection_stats_cache

        stats_cache = (
            Collection.objects.filter(client=obj)
            .aggregate(
                total_pick_ups=Count("id", filter=~Q(status=CollectionStatus.CANCELED)),
                last_pick_up=Max("collection_date", filter=~Q(status=CollectionStatus.CANCELED)),
                last_completed_pick_up=Max("collection_date", filter=Q(status=CollectionStatus.CONFIRMED)),
                total_paid=Sum("total_price", filter=Q(status=CollectionStatus.CONFIRMED, billable=True)),
            )
        )
        setattr(obj, "_collection_stats_cache", stats_cache)
        return stats_cache

    def get_frequency(self, obj):
        return obj.get_frequency_display()

    def get_total_pick_ups(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("total_pick_ups") or 0

    def get_last_pick_up(self, obj):
        stats = self._get_collection_stats(obj)
        dt = stats.get("last_pick_up")
        return dt or "-"

    def get_last_completed_pick_up(self, obj):
        stats = self._get_collection_stats(obj)
        dt = stats.get("last_completed_pick_up")
        return dt or "-"

    def get_total_paid(self, obj):
        stats = self._get_collection_stats(obj)
        total = stats.get("total_paid")
        return total or 0

    def get_email(self, obj):
        email = obj.user.email if obj.user else ""
        return "" if is_auto_generated_client_email(email) else email


class ClientUserOptionalWriteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255, trim_whitespace=True, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=255, required=False, allow_blank=True)

    def validate_username(self, value):
        cleaned_value = (value or "").strip()
        if cleaned_value and User.objects.filter(username=cleaned_value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese username.")
        return cleaned_value

    def validate_email(self, value):
        cleaned_value = (value or "").strip().lower()
        if cleaned_value and User.objects.filter(email__iexact=cleaned_value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return cleaned_value


class CreateClientSerializer(serializers.ModelSerializer):
    user = ClientUserOptionalWriteSerializer(required=False, default=dict)

    name = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    city = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    postal_code = serializers.CharField(required=True, max_length=10, trim_whitespace=True)
    country = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=False, allow_blank=True, max_length=20, trim_whitespace=True)

    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    get_access = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = Client
        fields = (
            "get_access",
            "user",
            "companies",
            "name",
            "address",
            "phone",
            "cif",
            "city",
            "postal_code",
            "country",
            "frequency",
        )

    def validate(self, attrs):
        user_data = attrs.get("user") or {}
        normalized_user_data = {
            "username": (user_data.get("username") or "").strip(),
            "email": (user_data.get("email") or "").strip().lower(),
        }
        attrs["user"] = normalized_user_data

        if attrs.get("get_access") and not normalized_user_data["email"]:
            raise serializers.ValidationError(
                {"user": {"email": "Debes indicar un email si quieres enviar acceso a la plataforma."}}
            )

        return attrs


class UpdateClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True, write_only=True)

    name = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=False, allow_blank=True, max_length=20, trim_whitespace=True)
    city = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    postal_code = serializers.CharField(required=True, max_length=10, trim_whitespace=True)
    country = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    class Meta:
        model = Client
        fields = (
            "name",
            "email",
            "address",
            "phone",
            "cif",
            "city",
            "postal_code",
            "country",
            "frequency",
        )

    def update(self, instance, validated_data):
        try:
            address_changed = (
                "address" in validated_data
                or "city" in validated_data
                or "postal_code" in validated_data
                or "country" in validated_data
            )
            email = validated_data.pop("email", None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if address_changed:
                sync_client_location_from_address(instance, clear_on_failure=True)

            if email and hasattr(instance, "user") and instance.user:
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"[client_serializers - update] Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")


class PartialUpdateClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True, write_only=True)

    name = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=False, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=False, allow_blank=True, max_length=20, trim_whitespace=True)
    city = serializers.CharField(required=False, max_length=100, trim_whitespace=True)
    postal_code = serializers.CharField(required=False, max_length=10, trim_whitespace=True)
    country = serializers.CharField(required=False, max_length=100, trim_whitespace=True)
    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    class Meta:
        model = Client
        fields = (
            "name",
            "email",
            "address",
            "phone",
            "cif",
            "city",
            "postal_code",
            "country",
            "frequency",
        )

    def update(self, instance, validated_data):
        try:
            address_changed = (
                "address" in validated_data
                or "city" in validated_data
                or "postal_code" in validated_data
                or "country" in validated_data
            )
            email = validated_data.pop("email", None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if address_changed:
                sync_client_location_from_address(instance, clear_on_failure=True)

            if email and hasattr(instance, "user") and instance.user:
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"[client_serializers - update] Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")

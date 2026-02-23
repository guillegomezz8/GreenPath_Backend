from rest_framework import serializers
from django.db.models import Sum, Count, Max
import logging

from apps.base.logger import configure_logging
from apps.user.api.serializers.user_nested_serializers import UserNestedWriteSerializer
from apps.user.models.client import Client
from apps.collection.models import Collection
from apps.base.enums import PickupFrequency, CollectionStatus

configure_logging()


class ClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    frequency = serializers.SerializerMethodField()
    total_pick_ups = serializers.SerializerMethodField()
    last_pick_up = serializers.SerializerMethodField()
    last_completed_pick_up = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = Client
        exclude = ("modified_date", "deleted_date", "created_date")

    def get_frequency(self, obj):
        return obj.get_frequency_display()

    def get_total_pick_ups(self, obj):
        return Collection.objects.filter(client=obj).count()

    def get_last_pick_up(self, obj):
        dt = (
            Collection.objects.filter(client=obj)
            .aggregate(dt=Max("collection_date"))
            .get("dt")
        )
        return dt or "-"

    def get_last_completed_pick_up(self, obj):
        dt = (
            Collection.objects.filter(client=obj, status=CollectionStatus.CONFIRMED)
            .aggregate(dt=Max("collection_date"))
            .get("dt")
        )
        return dt or "-"

    def get_total_paid(self, obj):
        total = (
            Collection.objects.filter(client=obj).aggregate(total=Sum("total_price")).get("total")
        )
        return total or 0


class CreateClientSerializer(serializers.ModelSerializer):
    user = UserNestedWriteSerializer(required=True)

    name = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    city = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    postal_code = serializers.CharField(required=True, max_length=10, trim_whitespace=True)
    country = serializers.CharField(required=True, max_length=100, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=True, max_length=20, trim_whitespace=True)

    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    get_access = serializers.BooleanField(required=True, write_only=True)

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


class UpdateClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)

    name = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
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
            email = validated_data.pop("email", None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if email and hasattr(instance, "user") and instance.user:
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"[client_serializers - update] Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")


class PartialUpdateClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)

    name = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=False, max_length=20, trim_whitespace=True)
    cif = serializers.CharField(required=False, max_length=20, trim_whitespace=True)
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
            email = validated_data.pop("email", None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if email and hasattr(instance, "user") and instance.user:
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"[client_serializers - update] Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")

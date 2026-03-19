import json

from rest_framework import serializers
from django.db.models import Sum, Count, Q
import logging

from apps.base.logger import configure_logging
from apps.base.enums import CollectionStatus, Role
from apps.user.api.serializers.user_nested_serializers import UserNestedWriteSerializer
from apps.user.models.client import Client
from apps.user.models.worker import Worker
from apps.route.models import Route

configure_logging()


class WorkerSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    assigned_trucks = serializers.SerializerMethodField()
    total_liters_collected = serializers.SerializerMethodField()
    total_routes = serializers.IntegerField(source="routes.count", read_only=True)
    total_collections = serializers.SerializerMethodField()
    confirmed_collections = serializers.SerializerMethodField()
    pending_collections = serializers.SerializerMethodField()
    canceled_collections = serializers.SerializerMethodField()
    total_incomes = serializers.SerializerMethodField()
    role = serializers.CharField(source="get_role_display", read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    disabled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Worker
        exclude = ("modified_date", "deleted_date", "created_date")

    def get_email(self, obj):
        return obj.user.email if obj.user else None

    def get_username(self, obj):
        return obj.user.username if obj.user else None

    def get_assigned_trucks(self, obj):
        if hasattr(obj, "truck") and obj.truck:
            brand = obj.truck.brand or ""
            model = obj.truck.model or ""
            return f"{obj.truck.registration_number} ({brand} {model})".strip()
        return "Sin asignar"

    def _get_collection_stats(self, obj):
        if hasattr(obj, "_collection_stats_cache"):
            return obj._collection_stats_cache

        stats_cache = obj.collections.aggregate(
            total_collections=Count("id", filter=~Q(status=CollectionStatus.CANCELED)),
            confirmed_collections=Count("id", filter=Q(status=CollectionStatus.CONFIRMED)),
            pending_collections=Count("id", filter=Q(status=CollectionStatus.PENDING_MEASUREMENT)),
            canceled_collections=Count("id", filter=Q(status=CollectionStatus.CANCELED)),
            total_liters_collected=Sum("net_liters", filter=Q(status=CollectionStatus.CONFIRMED)),
            total_incomes=Sum("total_price", filter=Q(status=CollectionStatus.CONFIRMED)),
        )
        obj._collection_stats_cache = stats_cache
        return stats_cache

    def get_total_liters_collected(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("total_liters_collected") or 0

    def get_total_incomes(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("total_incomes") or 0

    def get_total_collections(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("total_collections") or 0

    def get_confirmed_collections(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("confirmed_collections") or 0

    def get_pending_collections(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("pending_collections") or 0

    def get_canceled_collections(self, obj):
        stats = self._get_collection_stats(obj)
        return stats.get("canceled_collections") or 0


class CreateWorkerSerializer(serializers.ModelSerializer):
    user = UserNestedWriteSerializer(required=True)

    name = serializers.CharField(required=True, max_length=255, allow_blank=False, trim_whitespace=True)
    surname = serializers.CharField(required=True, max_length=255, allow_blank=False, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, allow_blank=False, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, allow_blank=False, trim_whitespace=True)
    dni = serializers.CharField(required=True, max_length=255, allow_blank=False, trim_whitespace=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    get_access = serializers.BooleanField(required=True, write_only=True)

    role = serializers.ChoiceField(choices=Role.choices, required=False, default=Role.WORKER)

    class Meta:
        model = Worker
        fields = (
            "get_access",
            "user",
            "role",
            "company",
            "name",
            "surname",
            "address",
            "phone",
            "dni",
            "birth_date",
            "photo",
        )

    def to_internal_value(self, data):
        normalized_data = {key: data.get(key) for key in data.keys()} if hasattr(data, "keys") else dict(data)
        user_data = normalized_data.get("user")
        if isinstance(user_data, str):
            try:
                normalized_data["user"] = json.loads(user_data)
            except json.JSONDecodeError:
                pass
        return super().to_internal_value(normalized_data)

    def validate_phone(self, v):
        v = (v or "").strip()
        if len(v) > 20:
            raise serializers.ValidationError("Teléfono: máximo 20 caracteres.")
        return v


class UpdateWorkerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)

    name = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    surname = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=True, max_length=20, trim_whitespace=True)
    dni = serializers.CharField(required=True, max_length=255, trim_whitespace=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    role = serializers.ChoiceField(choices=Role.choices, required=False)

    class Meta:
        model = Worker
        fields = (
            "role",
            "company",
            "name",
            "surname",
            "address",
            "phone",
            "dni",
            "photo",
            "email",
            "birth_date",
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
            logging.error(f"[worker_serializers - update] Error updating worker with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando trabajador: {str(e)}")


class PartialUpdateWorkerSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, write_only=True)

    name = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    surname = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    address = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(required=False, max_length=20, trim_whitespace=True)
    dni = serializers.CharField(required=False, max_length=255, trim_whitespace=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    role = serializers.ChoiceField(choices=Role.choices, required=False)

    class Meta:
        model = Worker
        fields = (
            "role",
            "company",
            "name",
            "surname",
            "address",
            "phone",
            "dni",
            "photo",
            "email",
            "birth_date",
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
            logging.error(f"[worker_serializers - update] Error updating worker with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando trabajador: {str(e)}")
   
        
class ClientSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name"]


class RouteSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "name"]


class MonthlyDataSerializer(serializers.Serializer):
    liters = serializers.DecimalField(max_digits=10, decimal_places=2)
    income = serializers.DecimalField(max_digits=10, decimal_places=2)


class DashboardSerializer(serializers.Serializer):
    clients = ClientSimpleSerializer(many=True)
    workers = WorkerSerializer(many=True)
    routes = RouteSimpleSerializer(many=True)
    dashboard = serializers.DictField(child=MonthlyDataSerializer())

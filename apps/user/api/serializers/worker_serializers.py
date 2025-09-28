from rest_framework import serializers
from django.db.models import Sum, Count
import logging

from apps.base.logger import configure_logging
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
    total_routes = serializers.IntegerField(source='routes.count', read_only=True)
    total_collections = serializers.IntegerField(source='collections.count', read_only=True)
    total_incomes = serializers.SerializerMethodField()
    role = serializers.CharField(source='get_role_display', read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    disabled = serializers.BooleanField(read_only=True)

    class Meta:
        model = Worker
        exclude = ("modified_date", "deleted_date", "created_date")

    def get_email(self, obj):
        return getattr(obj.user, "email", None)

    def get_username(self, obj):
        return getattr(obj.user, "username", None)

    def get_assigned_trucks(self, obj):
        if hasattr(obj, "truck") and obj.truck:
            brand = obj.truck.brand or ""
            model = obj.truck.model or ""
            return f"{obj.truck.registration_number} ({brand} {model})".strip()
        return "Sin asignar"

    def get_total_liters_collected(self, obj):
        agg = obj.collections.aggregate(total=Sum("liters_collected"))
        return agg["total"] or 0

    def get_total_incomes(self, obj):
        agg = obj.collections.aggregate(total=Sum("total_price"))
        return agg["total"] or 0


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

    role = serializers.CharField(required=False, allow_blank=False, max_length=10)

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

    role = serializers.CharField(required=False, allow_blank=False, max_length=10)

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

            if email and getattr(instance, "user", None):
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"Error updating worker with id {instance.id}: {str(e)}")
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
    role = serializers.CharField(required=False, allow_blank=False, max_length=10)

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

            if email and getattr(instance, "user", None):
                instance.user.email = email
                instance.user.full_clean(validate_unique=False)
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"Error updating worker with id {instance.id}: {str(e)}")
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

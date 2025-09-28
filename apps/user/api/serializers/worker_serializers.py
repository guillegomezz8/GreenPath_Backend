from rest_framework import serializers

import logging

from apps.base.logger import configure_logging
from apps.user.api.serializers.user_nested_serializers import UserNestedWriteSerializer
from apps.user.models.worker import Worker
from apps.user.models.client import Client
from apps.route.models import Route

configure_logging()


class WorkerSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, allow_null=True)
    email = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    assigned_trucks = serializers.SerializerMethodField()
    total_liters_collected = serializers.SerializerMethodField()
    total_routes = serializers.IntegerField(source='routes.count', read_only=True)
    total_collections = serializers.IntegerField(source='collections.count', read_only=True)
    total_incomes = serializers.SerializerMethodField()
    disabled = serializers.BooleanField()
    role = serializers.CharField(source='get_role_display', read_only=True)    

    class Meta:
        model = Worker
        exclude = ('modified_date', 'deleted_date', 'created_date')

    def get_email(self, obj):
        return obj.user.email

    def get_username(self, obj):
        return obj.user.username
    
    def get_assigned_trucks(self, obj):
        if hasattr(obj, 'truck'):
            return f"{obj.truck.registration_number} ({obj.truck.brand} {obj.truck.model})"
        return "Sin asignar"

    def get_total_liters_collected(self, obj):
        total = 0
        collections = obj.collections.all()
        for collection in collections:
            total += collection.liters_collected
        return total
    
    def get_total_incomes(self, obj):
        total = 0
        collections = obj.collections.all()
        for collection in collections:
            total += collection.total_price
        return total

class CreateWorkerSerializer(serializers.ModelSerializer):
    get_access = serializers.BooleanField(required=True, write_only=True)
    user = UserNestedWriteSerializer(required=True)
    
    name = serializers.CharField(required=True)
    surname = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    dni = serializers.CharField(required=True)
    birth_date = serializers.DateField(required=False)
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Worker
        fields = ('get_access', 'user', 'role',
                  'company', 'name', 'surname', 
                  'address', 'phone', 'dni',
                  'birth_date', 'photo')


class UpdateWorkerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    surname = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    dni = serializers.CharField(required=True)
    birth_date = serializers.DateField(required=False)
    photo = serializers.ImageField(required=False, allow_null=True)

    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'address', 'phone', 'dni', 'photo', 'email', 'birth_date')

    def update(self, instance, validated_data):
        try:
            user_data = validated_data.pop('user', {})
            email = user_data.get('email')

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            if email and hasattr(instance, 'user'):
                instance.user.email = email
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"Error updating worker with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating worker: {str(e)}")


class PartialUpdateWorkerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    surname = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    dni = serializers.CharField(required=False)
    birth_date = serializers.DateField(required=False)
    photo = serializers.ImageField(required=False, allow_null=True)

    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'address', 'phone', 'dni', 'photo', 'email', 'birth_date')

    def update(self, instance, validated_data):
        try:
            user_data = validated_data.pop('user', {})
            email = user_data.get('email')

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()

            if email and hasattr(instance, 'user'):
                instance.user.email = email
                instance.user.save(update_fields=["email"])

            return instance
        except Exception as e:
            logging.error(f"Error updating worker with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating worker: {str(e)}")


class ClientSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name']


class RouteSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'name']


class MonthlyDataSerializer(serializers.Serializer):
    liters = serializers.DecimalField(max_digits=10, decimal_places=2)
    income = serializers.DecimalField(max_digits=10, decimal_places=2)


class DashboardSerializer(serializers.Serializer):
    clients = ClientSimpleSerializer(many=True)
    workers = WorkerSerializer(many=True)
    routes = RouteSimpleSerializer(many=True)
    dashboard = serializers.DictField(child=MonthlyDataSerializer())
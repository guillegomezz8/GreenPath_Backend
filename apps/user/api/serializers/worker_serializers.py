from rest_framework import serializers
from apps.user.models.worker import Worker
from apps.user.models.client import Client
from apps.route.models import Route
import logging
from apps.base.logger import configure_logging

configure_logging()


class WorkerSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Worker
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateWorkerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    surname = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    dni = serializers.CharField(required=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Worker
        fields = ('user', 'role', 'company', 'name', 'surname', 'address', 'phone', 'dni', 'photo')

    def create(self, validated_data):
        try:
            worker = Worker.objects.create(**validated_data)
            return worker
        except Exception as e:
            logging.error(f"Error creating worker: {str(e)}")
            raise serializers.ValidationError(f"Error creating worker: {str(e)}")


class UpdateWorkerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    surname = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    dni = serializers.CharField(required=True)
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'address', 'phone', 'dni', 'photo')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
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
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'address', 'phone', 'dni', 'photo')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
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
from rest_framework import serializers
from apps.user.models.worker import Worker
import logging
from apps.base.logger import configure_logging

configure_logging()


class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ('user', 'role', 'company', 'name', 'surname', 'adress', 'phone', 'dni')

    def create(self, validated_data):
        try:
            worker = Worker.objects.create(**validated_data)
            return worker
        except Exception as e:
            logging.error(f"Error creating worker: {str(e)}")
            raise serializers.ValidationError(f"Error creating worker: {str(e)}")


class UpdateWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'adress', 'phone', 'dni')

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
    class Meta:
        model = Worker
        fields = ('role', 'company', 'name', 'surname', 'adress', 'phone', 'dni')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating worker with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating worker: {str(e)}")

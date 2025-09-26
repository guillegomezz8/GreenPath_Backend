from rest_framework import serializers

import logging

from apps.base.logger import configure_logging
from apps.user.api.serializers.user_nested_serializers import UserNestedWriteSerializer
from apps.user.models.client import Client
from apps.collection.models import Collection
from apps.base.enums import PickupFrequency
from apps.base.enums import CollectionStatus

configure_logging()


class ClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    frequency = serializers.SerializerMethodField()
    total_pick_ups = serializers.SerializerMethodField()
    last_pick_up = serializers.SerializerMethodField()
    last_completed_pick_up = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    def get_frequency(self, obj):
        return obj.get_frequency_display()

    def get_total_pick_ups(self, obj):
        return Collection.objects.filter(client=obj).count()
    
    def get_last_pick_up(self, obj):
        last_pick_up = Collection.objects.filter(client=obj).order_by('-collection_date').first()
        return last_pick_up.collection_date if last_pick_up else "-"
    
    def get_last_completed_pick_up(self, obj):
        last_completed_pick_up = Collection.objects.filter(client=obj, status=CollectionStatus.COMPLETED).order_by('-collection_date').first()
        return last_completed_pick_up.collection_date if last_completed_pick_up else "-"
    
    def get_total_paid(self, obj):
        total = 0
        collections = Collection.objects.filter(client=obj)
        for collection in collections:
            total += collection.total_price
        return total

    class Meta:
        model = Client
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateClientSerializer(serializers.ModelSerializer):
    get_access = serializers.BooleanField(required=True, write_only=True)
    user = UserNestedWriteSerializer(required=True)

    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)

    class Meta:
        model = Client
        fields = (
            'get_access', 'user', 'companies',
            'name', 'address', 'phone', 'cif',
            'city', 'postal_code', 'country', 'frequency'
        )


class UpdateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)

    email = serializers.EmailField(source='user.email', required=False)

    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    class Meta:
        model = Client
        fields = (
            'name', 'email', 'address', 'phone', 'cif',
            'city', 'postal_code', 'country', 'frequency'
        )

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
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")


class PartialUpdateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    cif = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    country = serializers.CharField(required=False)

    email = serializers.EmailField(source='user.email', required=False)

    frequency = serializers.ChoiceField(choices=PickupFrequency.choices, required=False)

    class Meta:
        model = Client
        fields = (
            'name', 'email', 'address', 'phone', 'cif',
            'city', 'postal_code', 'country', 'frequency'
        )

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
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")
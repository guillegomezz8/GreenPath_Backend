import logging

from rest_framework import serializers

from apps.base.literals import COLLECTION_REQUEST_FINAL_LITERS_REQUIRED, COLLECTION_REQUEST_FINAL_LITERS_INVALID
from apps.base.logger import configure_logging
from apps.collection.models import Collection, CollectionRequest

configure_logging()


class CollectionSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.name', read_only=True)
    route_name = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        exclude = ('modified_date', 'deleted_date', 'created_date')

    def get_status(self, obj):
        return obj.get_status_display()

    def get_route_name(self, obj):
        route = obj.route
        if not route:
            return None
        return route.name


class CreateCollectionSerializer(serializers.ModelSerializer):
    collection_date = serializers.DateField(required=True)
    price_per_liter = serializers.DecimalField(max_digits=7, decimal_places=3, required=False)
    measured_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deduction_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Collection
        fields = (
            'client',
            'route_day_client',
            'worker',
            'collection_date',
            'container_type',
            'container_number',
            'measured_liters',
            'deduction_liters',
            'deduction_reason',
            'deduction_notes',
            'price_per_liter',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def create(self, validated_data):
        try:
            collection = Collection.objects.create(**validated_data)
            return collection
        except Exception as e:
            logging.error(f'[collection_serializers - create] Error creating collection: {str(e)}')
            raise serializers.ValidationError(f'Error creating collection: {str(e)}')


class UpdateCollectionSerializer(serializers.ModelSerializer):
    collection_date = serializers.DateField(required=True)
    price_per_liter = serializers.DecimalField(max_digits=7, decimal_places=3, required=True)
    measured_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deduction_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Collection
        fields = (
            'client',
            'route_day_client',
            'worker',
            'collection_date',
            'container_type',
            'container_number',
            'measured_liters',
            'deduction_liters',
            'deduction_reason',
            'deduction_notes',
            'price_per_liter',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f'[collection_serializers - update] Error updating collection with id {instance.id}: {str(e)}')
            raise serializers.ValidationError(f'Error updating collection: {str(e)}')


class PartialUpdateCollectionSerializer(serializers.ModelSerializer):
    collection_date = serializers.DateField(required=False)
    price_per_liter = serializers.DecimalField(max_digits=7, decimal_places=3, required=False)
    measured_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deduction_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Collection
        fields = (
            'client',
            'route_day_client',
            'worker',
            'collection_date',
            'container_type',
            'container_number',
            'measured_liters',
            'deduction_liters',
            'deduction_reason',
            'deduction_notes',
            'price_per_liter',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f'[collection_serializers - update] Error updating collection with id {instance.id}: {str(e)}')
            raise serializers.ValidationError(f'Error updating collection: {str(e)}')


class AnswerCollectionRequestSerializer(serializers.Serializer):
    final_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    def validate_final_liters(self, value):
        if value is None:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_REQUIRED)
        if value <= 0:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_INVALID)
        return value


class ManualCollectionRequestSerializer(serializers.Serializer):
    final_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    def validate_final_liters(self, value):
        if value is None:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_REQUIRED)
        if value <= 0:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_INVALID)
        return value


class CollectionRequestSerializer(serializers.ModelSerializer):
    client_id = serializers.IntegerField(source="route_day_client.client_id", read_only=True)
    client_name = serializers.CharField(source="route_day_client.client.name", read_only=True)
    route_day_date = serializers.DateField(source="route_day_client.route_day.date", read_only=True)
    route_id = serializers.IntegerField(source="route_day_client.route_day.route_id", read_only=True)
    route_name = serializers.CharField(source="route_day_client.route_day.route.name", read_only=True)

    answered_by = serializers.IntegerField(source="answered_by_id", read_only=True)
    answered_by_username = serializers.CharField(source="answered_by.username", read_only=True)
    manual_by = serializers.IntegerField(source="manual_by_id", read_only=True)
    manual_by_username = serializers.CharField(source="manual_by.username", read_only=True)

    class Meta:
        model = CollectionRequest
        fields = (
            'id',
            'route_day_client',
            'client_id',
            'client_name',
            'route_day_date',
            'route_id',
            'route_name',
            'expires_at',
            'status',
            'container_type',
            'container_number',
            'estimated_liters',
            'final_liters',
            'final_source',
            'answered_by',
            'answered_by_username',
            'answered_at',
            'manual_by',
            'manual_by_username',
            'manual_at',
            'auto_estimate_task_id',
            'auto_estimate_scheduled_at',
        )

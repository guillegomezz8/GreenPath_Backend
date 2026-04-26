import logging

from rest_framework import serializers

from decimal import Decimal

from apps.base.enums import CollectionStatus, ContainerType, DeductionReason
from apps.base.literals import COLLECTION_REQUEST_FINAL_LITERS_REQUIRED, COLLECTION_REQUEST_FINAL_LITERS_INVALID
from apps.base.logger import configure_logging
from apps.company.utils import resolve_default_collection_price_per_liter
from apps.collection.models import Collection, CollectionRequest
from apps.collection.utils import container_capacity_liters

configure_logging()


class CollectionSerializer(serializers.ModelSerializer):
    client = serializers.IntegerField(source='client_id', read_only=True)
    worker = serializers.IntegerField(source='worker_id', read_only=True)
    route_day_client = serializers.IntegerField(source='route_day_client_id', read_only=True)
    status = serializers.SerializerMethodField()
    status_code = serializers.CharField(source='status', read_only=True)
    deduction_reason_label = serializers.CharField(source='get_deduction_reason_display', read_only=True)
    billable_label = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='client.name', read_only=True)
    route_name = serializers.SerializerMethodField()
    worker_name = serializers.SerializerMethodField()

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

    def get_worker_name(self, obj):
        worker = obj.worker
        if not worker:
            return None
        full_name = f"{worker.name or ''} {worker.surname or ''}".strip()
        if full_name:
            return full_name
        if hasattr(worker, "user") and worker.user:
            return worker.user.username
        return None

    def get_billable_label(self, obj):
        return "Facturable" if obj.billable else "No facturable"


def _normalize_collection_validated_data(validated_data, partial=False):
    status_provided = "status" in validated_data
    status_value = validated_data.get("status")
    measured_liters = validated_data.get("measured_liters")

    if status_value == CollectionStatus.CANCELED:
        return validated_data

    if status_provided:
        return validated_data

    if measured_liters is not None:
        validated_data["status"] = CollectionStatus.CONFIRMED
        return validated_data

    if not partial and status_value is None:
        validated_data["status"] = CollectionStatus.PENDING_MEASUREMENT
    return validated_data


def _update_collection_preserving_paid_total(instance, validated_data):
    original_total_price = instance.total_price
    for attr, value in validated_data.items():
        setattr(instance, attr, value)
    instance.save()

    if instance.total_price != original_total_price:
        Collection.objects.filter(pk=instance.pk).update(total_price=original_total_price)
        instance.total_price = original_total_price

    return instance


def _apply_default_price_per_liter(validated_data):
    if "price_per_liter" in validated_data and validated_data.get("price_per_liter") is not None:
        return validated_data

    default_price = resolve_default_collection_price_per_liter(
        client=validated_data.get("client"),
        worker=validated_data.get("worker"),
        route_day_client=validated_data.get("route_day_client"),
    )
    if default_price is not None:
        validated_data["price_per_liter"] = default_price
    return validated_data


class CreateCollectionSerializer(serializers.ModelSerializer):
    collection_date = serializers.DateField(required=True)
    price_per_liter = serializers.DecimalField(max_digits=7, decimal_places=3, required=False)
    measured_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deduction_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    deduction_reason = serializers.ChoiceField(choices=DeductionReason.choices, required=False, allow_blank=True)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)
    billable = serializers.BooleanField(required=False, default=True)

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
            'billable',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def create(self, validated_data):
        try:
            validated_data = _apply_default_price_per_liter(validated_data)
            validated_data = _normalize_collection_validated_data(validated_data)
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
    deduction_reason = serializers.ChoiceField(choices=DeductionReason.choices, required=False, allow_blank=True)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)
    billable = serializers.BooleanField(required=False)

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
            'billable',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def update(self, instance, validated_data):
        try:
            validated_data = _normalize_collection_validated_data(validated_data)
            return _update_collection_preserving_paid_total(instance, validated_data)
        except Exception as e:
            logging.error(f'[collection_serializers - update] Error updating collection with id {instance.id}: {str(e)}')
            raise serializers.ValidationError(f'Error updating collection: {str(e)}')


class PartialUpdateCollectionSerializer(serializers.ModelSerializer):
    collection_date = serializers.DateField(required=False)
    price_per_liter = serializers.DecimalField(max_digits=7, decimal_places=3, required=False)
    measured_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    deduction_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    deduction_reason = serializers.ChoiceField(choices=DeductionReason.choices, required=False, allow_blank=True)
    deduction_notes = serializers.CharField(required=False, allow_blank=True)
    billable = serializers.BooleanField(required=False)

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
            'billable',
            'status',
            'notes',
            'estimated_liters',
            'net_liters',
            'total_price',
        )
        read_only_fields = ('estimated_liters', 'net_liters', 'total_price')

    def update(self, instance, validated_data):
        try:
            validated_data = _normalize_collection_validated_data(validated_data, partial=True)
            return _update_collection_preserving_paid_total(instance, validated_data)
        except Exception as e:
            logging.error(f'[collection_serializers - update] Error updating collection with id {instance.id}: {str(e)}')
            raise serializers.ValidationError(f'Error updating collection: {str(e)}')


class AnswerCollectionRequestSerializer(serializers.Serializer):
    container_type = serializers.ChoiceField(choices=ContainerType.choices, required=False, default=ContainerType.BIDONES)
    container_number = serializers.IntegerField(min_value=1, required=False)
    final_liters = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, attrs):
        container_number = attrs.get("container_number")
        final_liters = attrs.get("final_liters")

        if container_number is not None:
            capacity = container_capacity_liters(attrs.get("container_type") or ContainerType.BIDONES)
            attrs["final_liters"] = (Decimal(container_number) * capacity).quantize(Decimal("0.01"))
            return attrs

        if final_liters is None:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_REQUIRED)
        if final_liters <= 0:
            raise serializers.ValidationError(COLLECTION_REQUEST_FINAL_LITERS_INVALID)
        return attrs


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
            'created_date',
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

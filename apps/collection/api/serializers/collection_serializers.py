from rest_framework import serializers
from apps.collection.models import Collection
import logging
from apps.base.logger import configure_logging

configure_logging()


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateCollectionSerializer(serializers.ModelSerializer):

    collection_date = serializers.DateTimeField(required=True)
    price_per_liter = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        model = Collection
        fields = ('client', 'worker', 'route', 'collection_date', 'container_number', 'price_per_liter', 'total_price', 'status')

    def create(self, validated_data):
        try:
            collection = Collection.objects.create(**validated_data)
            return collection
        except Exception as e:
            logging.error(f"Error creating collection: {str(e)}")
            raise serializers.ValidationError(f"Error creating collection: {str(e)}")


class UpdateCollectionSerializer(serializers.ModelSerializer):

    collection_date = serializers.DateTimeField(required=True)
    liters_collected = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    price_per_liter = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        model = Collection
        fields = ('client', 'worker', 'route', 'collection_date', 'liters_collected', 'price_per_liter', 'total_price', 'status')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating collection with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating collection: {str(e)}")


class PartialUpdateCollectionSerializer(serializers.ModelSerializer):

    collection_date = serializers.DateTimeField(required=False)
    liters_collected = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_per_liter = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = Collection
        fields = ('client', 'worker', 'route', 'collection_date', 'liters_collected', 'price_per_liter', 'total_price', 'status')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating collection with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating collection: {str(e)}")

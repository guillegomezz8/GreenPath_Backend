from rest_framework import serializers
from apps.route.models import Route
import logging
from apps.base.logger import configure_logging

configure_logging()


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateRouteSerializer(serializers.ModelSerializer):

    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)

    class Meta:
        model = Route
        fields = ('company', 'workers', 'date', 'start_time', 'end_time', 'status')

    def create(self, validated_data):
        try:
            route = Route.objects.create(**validated_data)
            return route
        except Exception as e:
            logging.error(f"Error creating route: {str(e)}")
            raise serializers.ValidationError(f"Error creating route: {str(e)}")


class UpdateRouteSerializer(serializers.ModelSerializer):

    date = serializers.DateField(required=True)
    start_time = serializers.TimeField(required=True)

    class Meta:
        model = Route
        fields = ('workers', 'date', 'start_time', 'end_time', 'status')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating route with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating route: {str(e)}")


class PartialUpdateRouteSerializer(serializers.ModelSerializer):

    date = serializers.DateField(required=False)
    start_time = serializers.TimeField(required=False)

    class Meta:
        model = Route
        fields = ('workers', 'date', 'start_time', 'end_time', 'status')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating route with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating route: {str(e)}")

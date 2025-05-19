from rest_framework import serializers
from apps.route.models import Route, RouteDay, RouteDayClient
from apps.user.api.serializers.client_serializers import ClientSerializer
import logging
from apps.base.logger import configure_logging

configure_logging()


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateRouteSerializer(serializers.ModelSerializer):

    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


    class Meta:
        model = Route
        fields = ('company', 'workers', 'start_date', 'end_date')

    def create(self, validated_data):
        try:
            route = Route.objects.create(**validated_data)
            return route
        except Exception as e:
            logging.error(f"Error creating route: {str(e)}")
            raise serializers.ValidationError(f"Error creating route: {str(e)}")


class UpdateRouteSerializer(serializers.ModelSerializer):

    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


    class Meta:
        model = Route
        fields = ('company', 'workers', 'start_date', 'end_date')

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

    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


    class Meta:
        model = Route
        fields = ('company', 'workers', 'start_date', 'end_date')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating route with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating route: {str(e)}")


class RouteDayClientSerializer(serializers.ModelSerializer):
    client = ClientSerializer()

    class Meta:
        model = RouteDayClient
        fields = ['client', 'order']


class RouteDaySerializer(serializers.ModelSerializer):
    ordered_clients = RouteDayClientSerializer(many=True, read_only=True)

    class Meta:
        model = RouteDay
        fields = ['id', 'route', 'date', 'name', 'ordered_clients']


class GenerateManualDayInputSerializer(serializers.Serializer):
    date = serializers.DateField()
    client_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )


class GenerateWeeklyRoutesFromClientsInputSerializer(serializers.Serializer):
    client_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="Lista de IDs de clientes a tener en cuenta para generar rutas semanales"
    )

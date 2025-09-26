from rest_framework import serializers
from datetime import date
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


class GenerateWeeklyZoneRoutesInputSerializer(serializers.Serializer):
    zone_config = serializers.DictField(
        child=serializers.ListField(
            child=serializers.CharField(max_length=100)
        ),
        help_text="Configuración de zonas por día. Clave: día de semana (0-6), Valor: lista de zonas"
    )
    max_clients_per_day = serializers.IntegerField(
        default=25,
        min_value=1,
        max_value=50,
        help_text="Máximo número de clientes por día"
    )

    def validate_zone_config(self, value):
        for key in value.keys():
            try:
                day = int(key)
                if day < 0 or day > 6:
                    raise serializers.ValidationError(
                        f"Día {key} no válido. Debe estar entre 0 (lunes) y 6 (domingo)"
                    )
            except ValueError:
                raise serializers.ValidationError(
                    f"Clave {key} no válida. Debe ser un número entre 0 y 6"
                )
        return value


class GenerateDailyZoneRouteInputSerializer(serializers.Serializer):
    date = serializers.DateField(
        help_text="Fecha para la ruta (formato: YYYY-MM-DD)"
    )
    zones = serializers.ListField(
        child=serializers.CharField(max_length=100),
        help_text="Lista de zonas para incluir en la ruta"
    )
    max_clients = serializers.IntegerField(
        default=25,
        min_value=1,
        max_value=50,
        help_text="Máximo número de clientes para esta ruta"
    )

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "La fecha no puede ser anterior a hoy"
            )
        return value

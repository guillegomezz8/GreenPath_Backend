from datetime import date, timedelta
from decimal import Decimal
import logging

from rest_framework import serializers

from apps.base.literals import (
    GENERATE_WEEK_CAPACITY_REQUIRED,
    GENERATE_WEEK_CAPACITY_MUTUALLY_EXCLUSIVE,
    GENERATE_WEEK_DAYS_DUPLICATED,
    GENERATE_WEEK_DAYS_OUTSIDE_WEEK,
    ROUTE_DAY_DATE_PAST_INVALID,
    ROUTE_ZONE_CONFIG_DAY_INVALID,
    ROUTE_ZONE_CONFIG_KEY_INVALID,
    ROUTE_END_DATE_BEFORE_START_DATE,
    ROUTE_WORKER_COMPANY_INVALID,
    ROUTE_ZONE_DAYS_DUPLICATED,
    ROUTE_ZONE_WEEKDAY_INVALID,
)
from apps.base.logger import configure_logging
from apps.route.models import Route, RouteDay, RouteDayClient
from apps.user.api.serializers.client_serializers import ClientSerializer
from apps.zone.models import Zone
from apps.base.enums import Weekday, ContainerType

configure_logging()


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateRouteSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Route
        fields = ('name', 'worker', 'start_date', 'end_date', 'week_start', 'week_end')
        extra_kwargs = {'worker': {'required': False}}

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(ROUTE_END_DATE_BEFORE_START_DATE)
        request = self.context.get('request')
        worker = attrs.get('worker')
        if worker and request and hasattr(request.user, 'worker_profile'):
            if worker.company_id != request.user.worker_profile.company_id:
                raise serializers.ValidationError(ROUTE_WORKER_COMPANY_INVALID)
        return attrs

    def create(self, validated_data):
        try:
            return Route.objects.create(**validated_data)
        except Exception as e:
            logging.error(f"[route_serializers - create] Error creating route: {str(e)}")
            raise serializers.ValidationError(f"Error creating route: {str(e)}")


class UpdateRouteSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Route
        fields = ('name', 'worker', 'start_date', 'end_date', 'week_start', 'week_end')
        extra_kwargs = {'worker': {'required': False}}

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        if start_date is None and self.instance is not None:
            start_date = self.instance.start_date
        end_date = attrs.get('end_date')
        if end_date is None and self.instance is not None:
            end_date = self.instance.end_date
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(ROUTE_END_DATE_BEFORE_START_DATE)
        request = self.context.get('request')
        worker = attrs.get('worker')
        if worker is None and self.instance is not None:
            worker = self.instance.worker
        if worker and request and hasattr(request.user, 'worker_profile'):
            if worker.company_id != request.user.worker_profile.company_id:
                raise serializers.ValidationError(ROUTE_WORKER_COMPANY_INVALID)
        return attrs

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"[route_serializers - update] Error updating route with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating route: {str(e)}")


class PartialUpdateRouteSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Route
        fields = ('name', 'worker', 'start_date', 'end_date', 'week_start', 'week_end')
        extra_kwargs = {'worker': {'required': False}}

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        if start_date is None and self.instance is not None:
            start_date = self.instance.start_date
        end_date = attrs.get('end_date')
        if end_date is None and self.instance is not None:
            end_date = self.instance.end_date
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(ROUTE_END_DATE_BEFORE_START_DATE)
        request = self.context.get('request')
        worker = attrs.get('worker')
        if worker is None and self.instance is not None:
            worker = self.instance.worker
        if worker and request and hasattr(request.user, 'worker_profile'):
            if worker.company_id != request.user.worker_profile.company_id:
                raise serializers.ValidationError(ROUTE_WORKER_COMPANY_INVALID)
        return attrs

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"[route_serializers - update] Error updating route with id {instance.id}: {str(e)}")
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
        fields = ['id', 'route', 'date', 'ordered_clients']


class GenerateWeeklyZoneRoutesInputSerializer(serializers.Serializer):
    zone_config = serializers.DictField(child=serializers.ListField(child=serializers.CharField(max_length=100)), help_text='Configuracion de zonas por dia. Clave: dia de semana (0-6), Valor: lista de zonas')
    max_clients_per_day = serializers.IntegerField(default=25, min_value=1, max_value=50, help_text='Maximo numero de clientes por dia')

    def validate_zone_config(self, value):
        for key in value.keys():
            try:
                day = int(key)
                if day < 0 or day > 6:
                    raise serializers.ValidationError(ROUTE_ZONE_CONFIG_DAY_INVALID)
            except ValueError:
                raise serializers.ValidationError(ROUTE_ZONE_CONFIG_KEY_INVALID)
        return value


class GenerateDailyZoneRouteInputSerializer(serializers.Serializer):
    date = serializers.DateField(help_text='Fecha para la ruta (formato: YYYY-MM-DD)')
    zones = serializers.ListField(child=serializers.CharField(max_length=100), help_text='Lista de zonas para incluir en la ruta')
    max_clients = serializers.IntegerField(default=25, min_value=1, max_value=50, help_text='Maximo numero de clientes para esta ruta')

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(ROUTE_DAY_DATE_PAST_INVALID)
        return value


class GenerateWeekDayCapacitySerializer(serializers.Serializer):
    date = serializers.DateField()
    daily_capacity_liters = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'))


class GenerateWeekSerializer(serializers.Serializer):
    week_start_date = serializers.DateField()
    regenerate = serializers.BooleanField(default=False, required=False)
    auto_estimate_without_contact = serializers.BooleanField(default=False, required=False)
    max_clients_per_day = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)
    daily_capacity_liters = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.00'), required=False, allow_null=True)
    days = GenerateWeekDayCapacitySerializer(many=True, required=False, allow_empty=False)

    def validate(self, attrs):
        global_capacity = attrs.get('daily_capacity_liters')
        days = attrs.get('days')

        if global_capacity is None and not days:
            raise serializers.ValidationError(GENERATE_WEEK_CAPACITY_REQUIRED)
        if global_capacity is not None and days:
            raise serializers.ValidationError(GENERATE_WEEK_CAPACITY_MUTUALLY_EXCLUSIVE)

        if days:
            week_start = attrs['week_start_date']
            week_end = week_start + timedelta(days=6)
            seen_dates = set()

            for day_config in days:
                day_date = day_config['date']
                if day_date in seen_dates:
                    raise serializers.ValidationError(GENERATE_WEEK_DAYS_DUPLICATED)
                seen_dates.add(day_date)
                if day_date < week_start or day_date > week_end:
                    raise serializers.ValidationError(GENERATE_WEEK_DAYS_OUTSIDE_WEEK)

        return attrs


class RouteZoneDayConfigItemSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    zones = serializers.PrimaryKeyRelatedField(queryset=Zone.objects.all(), many=True, required=False)


class RouteZoneConfigSerializer(serializers.Serializer):
    zone_days = RouteZoneDayConfigItemSerializer(many=True, required=False)

    def validate_zone_days(self, value):
        seen = set()
        for item in value:
            weekday = item.get('weekday')
            if weekday in seen:
                raise serializers.ValidationError(ROUTE_ZONE_DAYS_DUPLICATED)
            seen.add(weekday)
            if weekday not in Weekday.values:
                raise serializers.ValidationError(ROUTE_ZONE_WEEKDAY_INVALID)
        return value


class CompleteRouteDayClientSerializer(serializers.Serializer):
    container_type = serializers.ChoiceField(choices=ContainerType.choices, required=False, default=ContainerType.BIDONES)
    container_number = serializers.IntegerField(min_value=1, required=False, default=1)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    mark_as_canceled = serializers.BooleanField(required=False, default=False)
    force = serializers.BooleanField(required=False, default=False)
    worker_id = serializers.IntegerField(required=False, allow_null=True)


class FinishRouteDaySerializer(serializers.Serializer):
    close_action = serializers.ChoiceField(
        choices=[("PARTIAL", "Parcial"), ("CANCELED", "Cancelada")],
        required=False,
        allow_null=True,
    )

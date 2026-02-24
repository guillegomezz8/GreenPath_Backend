from datetime import datetime, timedelta
import logging

from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, DateFilter
from django.db.models import Q
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.literals import ERROR, ERROR_CREATING_ROUTE, ONLY_OWNERS_CAN_CREATE_ROUTES, DETAILS, NOT_ROUTE_IN_RANGE, INTERNAL_ERROR, MESSAGE, DATE_NOT_VALID, SUCCESFULY_GENERATE_ROUTES, WEEKLY_OPERATIONAL_ROUTE_GENERATED, ROUTE_ZONE_CONFIG_UPDATED
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser, IsRouteCompanyGenerator
from apps.route.api.serializers.route_serializers import RouteSerializer, CreateRouteSerializer, UpdateRouteSerializer, PartialUpdateRouteSerializer, RouteDaySerializer, GenerateWeeklyZoneRoutesInputSerializer, GenerateDailyZoneRouteInputSerializer, GenerateWeekSerializer, RouteZoneConfigSerializer
from apps.route.models import Route, RouteZoneDay, RouteDay
from apps.route.utils import generate_routes_for_date_range, generate_week_for_route

configure_logging()


class RouteFilter(FilterSet):
    date = DateFilter(field_name='route_days__date', lookup_expr='exact', distinct=True)
    status = CharFilter(field_name='route_days__status', lookup_expr='icontains', distinct=True)
    search = CharFilter(method='filter_search')

    class Meta:
        model = Route
        fields = ['date', 'status', 'search']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(company__name__icontains=value) |
            Q(workers__name__icontains=value) |
            Q(workers__surname__icontains=value)
        ).distinct()


class RouteViewSet(viewsets.ModelViewSet):
    model = Route
    queryset = Route.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RouteFilter

    def get_queryset(self):
        base_qs = super().get_queryset().prefetch_related('route_days')
        user = self.request.user

        if not user.is_authenticated:
            return base_qs.none()
        if user.is_staff or user.is_superuser:
            return base_qs
        if user.role_type in ['owner', 'worker'] and hasattr(user, "worker_profile"):
            return base_qs.filter(company_id=user.worker_profile.company_id)
        if user.role_type == 'client' and hasattr(user, "client_profile"):
            return base_qs.filter(route_days__ordered_clients__client_id=user.client_profile.id).distinct()
        return base_qs.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateRouteSerializer
        elif self.action == 'update':
            return UpdateRouteSerializer
        elif self.action == 'partial_update':
            return PartialUpdateRouteSerializer
        elif self.action == 'generate_weekly_zone_routes':
            return GenerateWeeklyZoneRoutesInputSerializer
        elif self.action == 'generate_daily_zone_route':
            return GenerateDailyZoneRouteInputSerializer
        elif self.action == 'generate_week':
            return GenerateWeekSerializer
        elif self.action == 'zone_config':
            return RouteZoneConfigSerializer
        return RouteSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'zone_config']:
            self.permission_classes = [IsOwnerUser]
        elif self.action in ['generate_week', 'generate_range_routes', 'operational_overview']:
            self.permission_classes = [IsAuthenticated, IsRouteCompanyGenerator]
        elif self.action == 'list':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(RouteViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                serializer.save(company=self.request.user.worker_profile.company)
            else:
                logging.error('[route_viewset - perform_create] Solo los duenos pueden crear rutas')
                raise ValueError(ONLY_OWNERS_CAN_CREATE_ROUTES)
        except Exception as e:
            logging.error(f'[route_viewset - perform_create] Error creando ruta: {str(e)}')
            raise Exception(f'{ERROR}: {ERROR_CREATING_ROUTE} - {str(e)}')

    @action(detail=True, methods=['post'], url_path='generate-range-routes')
    def generate_range_routes(self, request, pk=None):
        try:
            route = self.get_object()
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            zone_schedule = request.data.get('zone_schedule')
            max_clients = request.data.get('max_clients', 25)

            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            zone_schedule = {int(k): v for k, v in zone_schedule.items()}
            route_days = generate_routes_for_date_range(route, start_date=start_date, end_date=end_date, zone_schedule=zone_schedule, max_clients=max_clients)
            if not route_days:
                return Response({DETAILS: NOT_ROUTE_IN_RANGE}, status=status.HTTP_204_NO_CONTENT)
            serializer = RouteDaySerializer(route_days, many=True)
            logging.info('[route_viewset - generate_range_routes] Rutas generadas correctamente')
            return Response({MESSAGE: SUCCESFULY_GENERATE_ROUTES, 'routes': serializer.data}, status=status.HTTP_201_CREATED)
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f'[route_viewset - generate_range_routes] Datos de entrada no validos: {str(e)}')
            return Response({DETAILS: DATE_NOT_VALID}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f'[route_viewset - generate_range_routes] Error al generar rutas para rango de fechas: {str(e)}')
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='generate-week')
    def generate_week(self, request, pk=None):
        try:
            route = self.get_object()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated = serializer.validated_data
            route_days = generate_week_for_route(route=route, week_start_date=validated['week_start_date'], regenerate=validated.get('regenerate', False), daily_capacity_liters=validated.get('daily_capacity_liters'), days=validated.get('days') or [])
            payload = [{'id': route_day.id, 'date': route_day.date, 'daily_capacity_liters': route_day.daily_capacity_liters, 'stops': route_day.ordered_clients.count()} for route_day in route_days]
            logging.info(f'[route_viewset - generate_week] Semana operativa generada para ruta {route.id} con {len(payload)} dias')
            return Response({MESSAGE: WEEKLY_OPERATIONAL_ROUTE_GENERATED, 'route_days': payload}, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f'[route_viewset - generate_week] Error en generate_week: {str(e)}')
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get', 'put'], url_path='zone-config')
    def zone_config(self, request, pk=None):
        try:
            route = self.get_object()

            if request.method.lower() == 'get':
                zone_days_qs = RouteZoneDay.objects.filter(route=route).prefetch_related('zones').order_by('weekday')
                payload = []
                for zone_day in zone_days_qs:
                    zones = zone_day.zones.all()
                    payload.append({
                        'weekday': zone_day.weekday,
                        'zones': [{'id': zone.id, 'name': zone.name} for zone in zones],
                    })
                return Response({'zone_days': payload}, status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            zone_days_data = serializer.validated_data.get('zone_days') or []

            with transaction.atomic():
                requested_weekdays = set()
                for zone_day in zone_days_data:
                    weekday = zone_day['weekday']
                    zones = zone_day.get('zones', [])
                    requested_weekdays.add(weekday)
                    route_zone_day, _ = RouteZoneDay.objects.get_or_create(route=route, weekday=weekday)
                    route_zone_day.zones.set(zones)

                if requested_weekdays:
                    RouteZoneDay.objects.filter(route=route).exclude(weekday__in=requested_weekdays).delete()
                else:
                    RouteZoneDay.objects.filter(route=route).delete()

            zone_days_qs = RouteZoneDay.objects.filter(route=route).prefetch_related('zones').order_by('weekday')
            payload = []
            for zone_day in zone_days_qs:
                zones = zone_day.zones.all()
                payload.append({
                    'weekday': zone_day.weekday,
                    'zones': [{'id': zone.id, 'name': zone.name} for zone in zones],
                })
            logging.info(f'[route_viewset - zone_config] Configuracion de zonas actualizada para ruta {route.id}')
            return Response({MESSAGE: ROUTE_ZONE_CONFIG_UPDATED, 'zone_days': payload}, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f'[route_viewset - zone_config] Error gestionando zone_config: {str(e)}')
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='operational-overview')
    def operational_overview(self, request, pk=None):
        try:
            route = self.get_object()
            week_start_date = request.query_params.get('week_start_date')

            zone_days_qs = RouteZoneDay.objects.filter(route=route).prefetch_related('zones').order_by('weekday')
            zone_days_payload = []
            for zone_day in zone_days_qs:
                zones = zone_day.zones.all()
                zone_days_payload.append({
                    'weekday': zone_day.weekday,
                    'zones': [{'id': zone.id, 'name': zone.name} for zone in zones],
                })

            route_days_qs = (
                RouteDay.objects
                .filter(route=route)
                .select_related('route')
                .prefetch_related(
                    'ordered_clients__client',
                    'ordered_clients__collection_request',
                )
                .order_by('date')
            )

            if week_start_date:
                start_date = datetime.strptime(week_start_date, '%Y-%m-%d').date()
                end_date = start_date + timedelta(days=6)
                route_days_qs = route_days_qs.filter(date__gte=start_date, date__lte=end_date)

            route_days_payload = []
            for route_day in route_days_qs:
                ordered_clients = route_day.ordered_clients.all().order_by('order')
                clients_payload = []
                for row in ordered_clients:
                    request_obj = None
                    if hasattr(row, 'collection_request'):
                        request_obj = row.collection_request

                    clients_payload.append({
                        'route_day_client_id': row.id,
                        'order': row.order,
                        'client_id': row.client_id,
                        'client_name': row.client.name,
                        'client_address': row.client.address,
                        'collection_request': {
                            'id': request_obj.id if request_obj else None,
                            'status': request_obj.status if request_obj else None,
                            'expires_at': request_obj.expires_at if request_obj else None,
                            'estimated_liters': request_obj.estimated_liters if request_obj else None,
                            'final_liters': request_obj.final_liters if request_obj else None,
                            'final_source': request_obj.final_source if request_obj else None,
                        },
                    })

                route_days_payload.append({
                    'id': route_day.id,
                    'date': route_day.date,
                    'status': route_day.status,
                    'daily_capacity_liters': route_day.daily_capacity_liters,
                    'started_at': route_day.started_at,
                    'finished_at': route_day.finished_at,
                    'stops': len(clients_payload),
                    'clients': clients_payload,
                })

            response_payload = {
                'route': {
                    'id': route.id,
                    'name': route.name,
                    'company': route.company_id,
                    'workers': list(route.workers.values_list('id', flat=True)),
                    'start_date': route.start_date,
                    'end_date': route.end_date,
                    'week_start': route.week_start,
                    'week_end': route.week_end,
                },
                'zone_days': zone_days_payload,
                'route_days': route_days_payload,
            }
            return Response(response_payload, status=status.HTTP_200_OK)
        except ValueError as e:
            logging.error(f'[route_viewset - operational_overview] Fecha invalida en week_start_date: {str(e)}')
            return Response({DETAILS: DATE_NOT_VALID}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f'[route_viewset - operational_overview] Error obteniendo detalle operativo: {str(e)}')
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

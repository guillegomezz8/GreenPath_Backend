from datetime import datetime
import logging

from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter, DateFilter
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.literals import ERROR, ERROR_CREATING_ROUTE, ONLY_OWNERS_CAN_CREATE_ROUTES, DETAILS, NOT_ROUTE_IN_RANGE, INTERNAL_ERROR, MESSAGE, DATE_NOT_VALID, SUCCESFULY_GENERATE_ROUTES, WEEKLY_OPERATIONAL_ROUTE_GENERATED
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser, IsRouteCompanyGenerator
from apps.route.api.serializers.route_serializers import RouteSerializer, CreateRouteSerializer, UpdateRouteSerializer, PartialUpdateRouteSerializer, RouteDaySerializer, GenerateWeeklyZoneRoutesInputSerializer, GenerateDailyZoneRouteInputSerializer, GenerateWeekSerializer
from apps.route.models import Route
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
        base_qs = super().get_queryset()
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
        return RouteSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action in ['generate_week', 'generate_range_routes']:
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

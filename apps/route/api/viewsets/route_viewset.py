from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from apps.route.models import Route
from apps.base.permissions import IsOwnerUser
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
from apps.route.api.serializers.route_serializers import (
    RouteSerializer,
    CreateRouteSerializer,
    UpdateRouteSerializer,
    PartialUpdateRouteSerializer,
    RouteDaySerializer,
    GenerateWeeklyZoneRoutesInputSerializer,
    GenerateDailyZoneRouteInputSerializer
)
from apps.route.utils import generate_routes_for_date_range
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_ROUTE,
    ONLY_OWNERS_CAN_CREATE_ROUTES,
    DETAILS,
    NOT_ROUTE_IN_RANGE,
    INTERNAL_ERROR,
    MESSAGE,
    DATE_NOT_VALID,
    SUCCESFULY_GENERATE_ROUTES
)
import logging

configure_logging()


class RouteFilter(FilterSet):
    date = CharFilter(field_name='date', lookup_expr='icontains')
    status = CharFilter(field_name='status', lookup_expr='icontains')

    class Meta:
        model = Route
        fields = ['date', 'status']


class RouteViewSet(viewsets.ModelViewSet):
    model = Route
    queryset = Route.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = RouteFilter

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
        else:
            return RouteSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(RouteViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                serializer.save(company=self.request.user.worker_profile.company)
            else:
                logging.error("Solo los dueños pueden crear rutas")
                raise ValueError(ONLY_OWNERS_CAN_CREATE_ROUTES)
        except Exception as e:
            logging.error(f"Error creando ruta: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_ROUTE} - {str(e)}")

    @action(detail=True, methods=['post'], url_path='generate-range-routes')
    def generate_range_routes(self, request, pk=None):
        """
        POST /routes/{id}/generate-range-routes/
        Body JSON:
        {
            "start_date": "2025-01-01",
            "end_date": "2025-06-24",
            "zone_schedule": {
                "0": ["Nervión"],
                "1": ["Bermejales", "Los Remedios"]
            },
            "max_clients": 25
        }
        """
        route = self.get_object()

        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        zone_schedule = request.data.get("zone_schedule")
        max_clients = request.data.get("max_clients", 25)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            zone_schedule = {int(k): v for k, v in zone_schedule.items()}
        except Exception as e:
            logging.error(f"Datos de entrada no válidos: {e}")
            return Response({DETAILS: DATE_NOT_VALID}, status=400)

        try:
            route_days = generate_routes_for_date_range(
                route,
                start_date=start_date,
                end_date=end_date,
                zone_schedule=zone_schedule,
                max_clients=max_clients
            )

            if not route_days:
                return Response({DETAILS: NOT_ROUTE_IN_RANGE}, status=204)

            serializer = RouteDaySerializer(route_days, many=True)
            logging.info("Rutas generadas correctamente")
            return Response({
                MESSAGE: SUCCESFULY_GENERATE_ROUTES,
                "routes": serializer.data
            }, status=201)

        except Exception as e:
            logging.exception("Error al generar rutas para rango de fechas")
            return Response({DETAILS: f"{INTERNAL_ERROR} {str(e)}"}, status=500)
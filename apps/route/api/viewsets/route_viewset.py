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
from apps.route.utils import  generate_weekly_routes_from_clients, generate_manual_day_route
from datetime import datetime
from apps.route.models import RouteDay
from apps.route.api.serializers.route_serializers import (
    RouteSerializer,
    CreateRouteSerializer,
    UpdateRouteSerializer,
    PartialUpdateRouteSerializer,
    RouteDaySerializer,
    GenerateManualDayInputSerializer,
    GenerateWeeklyRoutesFromClientsInputSerializer
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_ROUTE
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
        elif self.action == 'generate_manual_day':
            return GenerateManualDayInputSerializer
        elif self.action == 'generate_weekly_routes_from_clients_action':
            return GenerateWeeklyRoutesFromClientsInputSerializer
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
                raise ValueError("Solo los dueños pueden crear rutas")
        except Exception as e:
            logging.error(f"Error creando ruta: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_ROUTE} - {str(e)}")
        
    @action(detail=True, methods=['post'], url_path='generate-weekly-routes-from-clients')
    def generate_weekly_routes_from_clients_action(self, request, pk=None):
        """
        POST /routes/{id}/generate-weekly-routes-from-clients/
        Body: { "client_ids": [1, 2, 3] }
        """
        route = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client_ids = serializer.validated_data["client_ids"]

        try:
            route_days = generate_weekly_routes_from_clients(route, client_ids)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        output_serializer = RouteDaySerializer(route_days, many=True)
        return Response(output_serializer.data, status=201)

    @action(detail=True, methods=['post'], url_path='generate-manual-day')
    def generate_manual_day(self, request, pk=None):
        route = self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        route_date = serializer.validated_data["date"]
        client_ids = serializer.validated_data["client_ids"]

        try:
            route_day = generate_manual_day_route(route, route_date, client_ids)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        output_serializer = RouteDaySerializer(route_day)
        return Response(output_serializer.data, status=201)


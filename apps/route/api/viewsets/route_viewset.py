from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from apps.route.models import Route
from apps.base.permissions import IsOwnerUser
from apps.route.api.serializers.route_serializers import (
    RouteSerializer,
    CreateRouteSerializer,
    UpdateRouteSerializer,
    PartialUpdateRouteSerializer
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

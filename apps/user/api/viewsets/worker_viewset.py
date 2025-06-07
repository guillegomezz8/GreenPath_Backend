from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from apps.user.models.worker import Worker
from apps.base.permissions import IsOwnerUser
from apps.user.api.serializers.worker_serializers import (
    WorkerSerializer,
    CreateWorkerSerializer,
    UpdateWorkerSerializer,
    PartialUpdateWorkerSerializer
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_WORKER
)
import logging

configure_logging()


class WorkerFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    surname = CharFilter(field_name='surname', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    dni = CharFilter(field_name='dni', lookup_expr='icontains')
    role = CharFilter(field_name='role', lookup_expr='icontains')

    class Meta:
        model = Worker
        fields = ['name', 'surname', 'phone', 'dni', 'role']


class WorkerViewSet(viewsets.ModelViewSet):
    model = Worker
    queryset = Worker.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = WorkerFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateWorkerSerializer
        elif self.action == 'update':
            return UpdateWorkerSerializer
        elif self.action == 'partial_update':
            return PartialUpdateWorkerSerializer
        else:
            return WorkerSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(WorkerViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                serializer.save(company=self.request.user.worker_profile.company)
            else:
                logging.error("Solo los dueños pueden crear trabajadores")
                raise ValueError("Solo los dueños pueden crear trabajadores")
        except Exception as e:
            logging.error(f"Error creando trabajador: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_WORKER} - {str(e)}")

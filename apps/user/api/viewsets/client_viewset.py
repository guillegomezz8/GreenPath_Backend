from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from apps.user.models.client import Client
from apps.base.permissions import IsOwnerUser
from apps.user.api.serializers.client_serializers import (
    ClientSerializer,
    CreateClientSerializer,
    UpdateClientSerializer,
    PartialUpdateClientSerializer
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_CLIENT
)
import logging

configure_logging()


class ClientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    cif = CharFilter(field_name='cif', lookup_expr='icontains')
    adress = CharFilter(field_name='adress', lookup_expr='icontains')

    class Meta:
        model = Client
        fields = ['name', 'phone', 'cif', 'adress']


class ClientViewSet(viewsets.ModelViewSet):
    model = Client
    parser_classes = (MultiPartParser, FormParser,)
    queryset = Client.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateClientSerializer
        elif self.action == 'update':
            return UpdateClientSerializer
        elif self.action == 'partial_update':
            return PartialUpdateClientSerializer
        else:
            return ClientSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(ClientViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                # Create the client
                client = serializer.save()
                # Add the owner's company to the client's companies
                if hasattr(self.request.user, 'worker_profile') and self.request.user.worker_profile.company:
                    client.companies.add(self.request.user.worker_profile.company)
            else:
                logging.error("Solo los dueños pueden crear clientes")
                raise ValueError("Solo los dueños pueden crear clientes")
        except Exception as e:
            logging.error(f"Error creando cliente: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_CLIENT} - {str(e)}")
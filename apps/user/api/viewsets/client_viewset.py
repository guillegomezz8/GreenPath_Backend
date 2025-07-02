from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
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
    ERROR_CREATING_CLIENT,
    DETAILS,
    ONLY_OWNERS_CAN_CREATE_CLIENTS,
    USER_COMPANY_DOES_NOT_EXIST
)
import logging

configure_logging()


class ClientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    cif = CharFilter(field_name='cif', lookup_expr='icontains')
    address = CharFilter(field_name='address', lookup_expr='icontains')

    class Meta:
        model = Client
        fields = ['name', 'phone', 'cif', 'address']


class ClientViewSet(viewsets.ModelViewSet):
    model = Client
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
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super(ClientViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                client = serializer.save()
                if hasattr(self.request.user, 'worker_profile') and self.request.user.worker_profile.company:
                    client.companies.add(self.request.user.worker_profile.company)
            else:
                logging.error("Solo los dueños pueden crear clientes")
                raise ValueError(ONLY_OWNERS_CAN_CREATE_CLIENTS)
        except Exception as e:
            logging.error(f"Error creando cliente: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_CLIENT} - {str(e)}")
    
    def list(self, request):
        try:
            company = request.user.worker_profile.company
            logging.info(f"Usuario {request.user.username} solicitando lista de clientes")
            if not company:
                if request.user.is_staff:
                    queryset = self.filter_queryset(self.get_queryset())
                    serializer = self.get_serializer(queryset, many=True)
                    logging.info("Listando todos los clientes para el usuario admin")
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    logging.error("El usuario no tiene una empresa asociada")
                    return Response({DETAILS: USER_COMPANY_DOES_NOT_EXIST}, status=400)
            queryset = self.filter_queryset(self.get_queryset().filter(companies=company))
            serializer = self.get_serializer(queryset, many=True)
            logging.info("Listando clientes para la empresa del usuario")
            return Response(serializer.data, status=200)
        except Exception as e:
            logging.error(f"Error al listar clientes: {str(e)}")
            return Response({DETAILS: str(e)}, status=400)
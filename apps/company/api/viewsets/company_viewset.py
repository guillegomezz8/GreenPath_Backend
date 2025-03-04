from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import (
    FilterSet, CharFilter,DjangoFilterBackend 
)
from apps.base.logger import configure_logging
from apps.company.models import Company
from apps.base.permissions import IsOwnerUser
from apps.company.api.serializers.company_serializers import (
    CompanySerializer,
    UpdateCompanySerializer,
    CreateCompanySerializer,
    PartialUpdateCompanySerializer
)
from apps.base.literals import(
    ERROR,
    ERROR_CREATING_COMPANY 
    )
import logging

configure_logging()


class CompanyFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    adress = CharFilter(field_name='adress', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')
    cif = CharFilter(field_name='cif', lookup_expr='icontains')

    class Meta:
        model = Company
        fields = ['name','address', 'phone', 'email', 'cif', ]


class CompanyViewSet(viewsets.ModelViewSet):
    model = Company
    queryset = Company.objects.all().order_by('id')
    parser_classes = (MultiPartParser, FormParser,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompanyFilter
    serializer_class = CompanySerializer

    # TODO: get_queryset un user solo puede ver la empresa a la que pertenece

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCompanySerializer
        elif self.action == 'update':
            return UpdateCompanySerializer
        elif self.action == 'partial_update':
            return PartialUpdateCompanySerializer
        else:
            return CompanySerializer 

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser, IsAuthenticated]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(CompanyViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                serializer.save(owner=self.request.user)
            else:
                logging.error("Solo los dueños pueden crear empresas")
                raise ValueError("Solo los dueños pueden crear empresas")
        except Exception as e:
            logging.error(f"Error creando empresa: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_COMPANY} - {str(e)}")


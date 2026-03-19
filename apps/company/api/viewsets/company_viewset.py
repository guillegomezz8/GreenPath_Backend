from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import (
    FilterSet, CharFilter,DjangoFilterBackend 
)
from django.db.models import Q
from apps.base.logger import configure_logging
from apps.company.models import Company
from apps.company.utils import get_or_create_company_settings, resolve_user_company
from apps.base.permissions import IsOwnerUser
from apps.company.api.serializers.company_serializers import (
    CompanySerializer,
    UpdateCompanySerializer,
    CreateCompanySerializer,
    PartialUpdateCompanySerializer,
    CompanySettingsSerializer,
)
from apps.base.literals import(
    ERROR,
    ERROR_CREATING_COMPANY,
    ONLY_OWNERS_CAN_CREATE_COMPANIES,
    COMPANY_SETTINGS_UPDATED,
    COMPANY_SETTINGS_FORBIDDEN,
    COMPANY_SETTINGS_UPDATE_FORBIDDEN,
    COMPANY_SETTINGS_NOT_FOUND,
    DETAILS,
    INTERNAL_ERROR,
    MESSAGE,
)
import logging

configure_logging()


class CompanyFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    address = CharFilter(field_name='address', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    email = CharFilter(field_name='email', lookup_expr='icontains')
    cif = CharFilter(field_name='cif', lookup_expr='icontains')
    search = CharFilter(method='filter_search')

    class Meta:
        model = Company
        fields = ['name', 'address', 'phone', 'email', 'cif', 'search']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(address__icontains=value) |
            Q(email__icontains=value) |
            Q(cif__icontains=value) |
            Q(phone__icontains=value)
        )


class CompanyViewSet(viewsets.ModelViewSet):
    model = Company
    queryset = Company.objects.all().order_by('id')
    filter_backends = [DjangoFilterBackend]
    filterset_class = CompanyFilter
    serializer_class = CompanySerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return base_qs.none()

        if user.is_staff or user.is_superuser:
            return base_qs

        if user.role_type == 'owner':
            if hasattr(user, 'worker_profile') and user.worker_profile.company_id:
                return base_qs.filter(id=user.worker_profile.company_id)
            return base_qs.filter(owner=user)

        return base_qs.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCompanySerializer
        elif self.action == 'update':
            return UpdateCompanySerializer
        elif self.action == 'partial_update':
            return PartialUpdateCompanySerializer
        elif self.action == 'company_settings':
            return CompanySettingsSerializer
        else:
            return CompanySerializer 

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'list', 'retrieve']:
            self.permission_classes = [IsOwnerUser, IsAuthenticated]
        elif self.action == 'company_settings':
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(CompanyViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner':
                serializer.save(owner=self.request.user)
            else:
                logging.error("[company_viewset - perform_create] Solo los dueños pueden crear empresas")
                raise ValueError(ONLY_OWNERS_CAN_CREATE_COMPANIES)
        except Exception as e:
            logging.error(f"[company_viewset - perform_create] Error creando empresa: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_COMPANY} - {str(e)}")

    @action(detail=False, methods=['get', 'put'], url_path='settings')
    def company_settings(self, request):
        try:
            company = resolve_user_company(request.user)
            if not company:
                logging.warning(f"[company_viewset - company_settings] Usuario {request.user.id} sin empresa asociada")
                return Response({DETAILS: COMPANY_SETTINGS_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role_type not in ['owner', 'worker']:
                logging.warning(f"[company_viewset - company_settings] Usuario {request.user.id} sin permiso para consultar configuracion")
                return Response({DETAILS: COMPANY_SETTINGS_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            settings_obj = get_or_create_company_settings(company)

            if request.method.lower() == 'get':
                serializer = self.get_serializer(settings_obj)
                logging.info(f"[company_viewset - company_settings] Configuracion consultada para empresa {company.id} por usuario {request.user.id}")
                return Response(serializer.data, status=status.HTTP_200_OK)

            if request.user.role_type != 'owner':
                logging.warning(f"[company_viewset - company_settings] Usuario {request.user.id} sin permiso para actualizar configuracion")
                return Response({DETAILS: COMPANY_SETTINGS_UPDATE_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(settings_obj, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logging.info(f"[company_viewset - company_settings] Configuracion actualizada para empresa {company.id} por usuario {request.user.id}")
            return Response({MESSAGE: COMPANY_SETTINGS_UPDATED, 'settings': serializer.data}, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[company_viewset - company_settings] Error gestionando configuracion de empresa: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


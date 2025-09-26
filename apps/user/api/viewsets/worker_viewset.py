from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny

import django_filters
from django_filters.rest_framework import FilterSet, CharFilter, DjangoFilterBackend, BooleanFilter
from django.db import transaction
from django.db.models import Q, Count

from datetime import datetime
import logging

from apps.base.logger import configure_logging
from apps.base.utils import gen_password, send_access_email
from apps.user.models.user import User
from apps.user.models.worker import Worker
from apps.base.permissions import IsOwnerUser
from apps.collection.api.serializers.collection_serializers import CollectionSerializer
from apps.user.api.serializers.worker_serializers import WorkerSerializer,CreateWorkerSerializer,UpdateWorkerSerializer,PartialUpdateWorkerSerializer,DashboardSerializer
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_WORKER,
    INTERNAL_ERROR,
    DETAILS,
    USER_COMPANY_DOES_NOT_EXIST,
    ONLY_OWNERS_CAN_CREATE_WORKERS,
    ERROR_GETTING_DASHBOARD_DATA
)

configure_logging()

AUX_MONTHS = {
    1: 'Enero',
    2: 'Febrero',
    3: 'Marzo',
    4: 'Abril',
    5: 'Mayo',
    6: 'Junio',
    7: 'Julio',
    8: 'Agosto',
    9: 'Septiembre',
    10: 'Octubre',
    11: 'Noviembre',
    12: 'Diciembre'
}


class WorkerFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    surname = CharFilter(field_name='surname', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    dni = CharFilter(field_name='dni', lookup_expr='icontains')
    role = CharFilter(field_name='role', lookup_expr='icontains')
    disabled = BooleanFilter(field_name='disabled')
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Worker
        fields = ['name', 'surname', 'phone', 'dni', 'role', 'disabled']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(surname__icontains=value)
        )


class WorkerViewSet(viewsets.ModelViewSet):
    model = Worker
    queryset = Worker.objects.all().order_by('id')
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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'get_collections']:
            self.permission_classes = [IsOwnerUser]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super(WorkerViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            logging.info(f"[worker_viewset - perform_create] Creando nuevo trabajador por usuario {self.request.user.id}")
            worker_data = dict(serializer.validated_data)
            user_data = worker_data.pop("user")
            get_access = worker_data.pop("get_access", False)
            companies = worker_data.pop("companies", None)

            company = getattr(getattr(self.request.user, "worker_profile", None), "company", None)

            with transaction.atomic():
                user = User.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=None,
                )

                temp_password = None
                if get_access:
                    temp_password = gen_password()
                    user.set_password(temp_password)
                    transaction.on_commit(lambda: send_access_email(user, temp_password, subject="Acceso a GreenPath como Trabajador"))
                else:
                    user.set_unusable_password()

                user.save(update_fields=["password"])

                worker = Worker.objects.create(user=user, **worker_data)

                if companies:
                    worker.companies.set(companies)

                if company:
                    worker.companies.add(company)

        except Exception as e:
            logging.error(f"[worker_viewset - perform_create] Error creando trabajador: {str(e)}")
            raise Exception({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)
        
    def perform_destroy(self, instance):
        try:
            logging.info(f"[worker_viewset - perform_destroy] Deshabilitando trabajador {instance.id} por usuario {self.request.user.id}")
            instance.disabled = True
            instance.save(update_fields=['disabled'])
            logging.info(f"[worker_viewset - perform_destroy] Trabajador deshabilitado con éxito: {instance.id}")
        except Exception as e:
            logging.error(f"[worker_viewset - perform_destroy] Error eliminando trabajador: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)
        
    def list(self, request):
        try:
            logging.info(f"[worker_viewset - list] Listando trabajadores para usuario {request.user.id}")
            base_queryset = self.get_queryset()
            filtered_queryset = self.filter_queryset(base_queryset)

            counts = base_queryset.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(disabled=False)),
                inactive=Count('id', filter=Q(disabled=True)),
            )

            page = self.paginate_queryset(filtered_queryset)

            if page is not None:
                items = page
                meta = {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                }
            else:
                items = filtered_queryset
                meta = {}

            serializer = self.get_serializer(items, many=True)

            response = {
                **meta,  
                "results": serializer.data,
                "counts": counts,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"[client_viewset - list] Error al listar clientes: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)
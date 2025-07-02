from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from datetime import datetime
from django.db.models import Sum
from apps.collection.models import Collection
from apps.user.models.worker import Worker
from apps.base.permissions import IsOwnerUser
from apps.user.api.serializers.worker_serializers import (
    WorkerSerializer,
    CreateWorkerSerializer,
    UpdateWorkerSerializer,
    PartialUpdateWorkerSerializer,
    DashboardSerializer
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_WORKER,
    DETAILS,
    USER_COMPANY_DOES_NOT_EXIST,
    ONLY_OWNERS_CAN_CREATE_WORKERS,
    ERROR_GETTING_DASHBOARD_DATA
)
import logging

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
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'dashboard']:
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
                raise ValueError(ONLY_OWNERS_CAN_CREATE_WORKERS)
        except Exception as e:
            logging.error(f"Error creando trabajador: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_WORKER} - {str(e)}")

    @action(detail=False, methods=['get'], url_path='dashboard')
    def owner_dashboard(self, request):
        logging.info(f"[Dashboard] Usuario accedió: {request.user}")

        try:
            company = request.user.worker_profile.company
        except AttributeError as e:
            logging.error(f"[Dashboard] Error accediendo a company desde el perfil de {request.user}: {e}")
            return Response({DETAILS: USER_COMPANY_DOES_NOT_EXIST}, status=status.HTTP_400_BAD_REQUEST)

        if not company:
            logging.error(f"[Dashboard] Usuario sin compañía: {request.user}")
            return Response({DETAILS: USER_COMPANY_DOES_NOT_EXIST}, status=status.HTTP_400_BAD_REQUEST)

        logging.info(f"[Dashboard] Generando datos para la compañía: {company.name} (ID: {company.id})")

        try:
            clients = company.clients
            workers = company.workers
            routes = company.routes

            logging.info(f"[Dashboard] Totales: {clients} clientes, {workers} trabajadores, {routes} rutas")

            dashboard_data = {}
            current_year = datetime.now().year

            for month, month_name in AUX_MONTHS.items():
                collections = Collection.objects.filter(
                    collection_date__month=month,
                    collection_date__year=current_year,
                    worker__company=company
                )

                liters = collections.aggregate(Sum('liters_collected'))['liters_collected__sum'] or 0
                income = collections.aggregate(Sum('total_price'))['total_price__sum'] or 0

                dashboard_data[month] = {
                    "liters": liters,
                    "income": income
                }

            serializer = DashboardSerializer({
                "clients": clients,
                "workers": workers,
                "routes": routes,
                "dashboard": dashboard_data
            })

            logging.info(f"[Dashboard] Datos generados correctamente para {company.name}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"[Dashboard] Error inesperado generando dashboard para {company.name}: {e}", exc_info=True)
            return Response({DETAILS: ERROR_GETTING_DASHBOARD_DATA}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
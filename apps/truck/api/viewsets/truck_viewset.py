from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import FilterSet, CharFilter, NumberFilter, DjangoFilterBackend

import logging

from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser
from apps.truck.models import Truck
from apps.user.models.worker import Worker
from apps.truck.api.serializers.truck_serializers import (
    TruckSerializer,
    CreateTruckSerializer,
    UpdateTruckSerializer,
    PartialUpdateTruckSerializer,
    AssignDriverSerializer
)
from apps.base.literals import (
    ERROR_CREATING_TRUCK,
    DETAILS,
    INTERNAL_ERROR,
    ONLY_OWNERS_CAN_CREATE_TRUCKS,
    NEED_COMPANY_FOR_TRUCK_CREATION,
    DRIVER_TRUCK_SAME_COMPANY,
    ONLY_UPDATE_TRUCKS_SAME_COMPANY,
    ALREADY_HAVE_DRIVER
)

configure_logging()


class TruckFilter(FilterSet):
    registration_number = CharFilter(field_name="registration_number", lookup_expr="icontains")
    brand = CharFilter(field_name="brand", lookup_expr="icontains")
    model = CharFilter(field_name="model", lookup_expr="icontains")
    status = CharFilter(field_name="status", lookup_expr="exact")
    fuel = CharFilter(field_name="fuel", lookup_expr="exact")

    year = NumberFilter(field_name="year", lookup_expr="exact")
    year_gte = NumberFilter(field_name="year", lookup_expr="gte")
    year_lte = NumberFilter(field_name="year", lookup_expr="lte")

    company = NumberFilter(field_name="company", lookup_expr="exact")
    driver = NumberFilter(field_name="driver", lookup_expr="exact")

    class Meta:
        model = Truck
        fields = ["registration_number", "brand", "model", "status", "fuel", "year", "company", "driver"]


def _user_company_id(user):
    return getattr(getattr(user, "worker_profile", None), "company_id", None)


class TruckViewSet(viewsets.ModelViewSet):
    model = Truck
    queryset = Truck.objects.all().order_by("id")
    filter_backends = [DjangoFilterBackend]
    filterset_class = TruckFilter
    serializer_class = TruckSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return qs.none()

        if user.is_staff or user.is_superuser:
            return qs

        company_id = _user_company_id(user)
        if company_id:
            return qs.filter(company_id=company_id)
        return qs.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateTruckSerializer
        elif self.action == "update":
            return UpdateTruckSerializer
        elif self.action == "partial_update":
            return PartialUpdateTruckSerializer
        if self.action == "assign_driver":
            return AssignDriverSerializer
        else:
            return TruckSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [IsOwnerUser, IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(TruckViewSet, self).get_permissions()

    def _validate_driver_same_company(self, *, company, driver):
        if driver is None:
            return False
        drv_company_id = driver.company_id
        if drv_company_id is None or company is None or drv_company_id != company.id:
            logging.error("[truck_viewset - _validate_driver_same_company] El conductor debe pertenecer a la misma empresa que el camión.")
            return False
        return True

    def perform_create(self, serializer):
        try:
            company = serializer.validated_data.get("company")
            driver = serializer.validated_data.get("driver")

            if not company:
                logging.error("[truck_viewset - perform_create] Debe especificar la empresa (company) para crear un camión.")
                return Response({DETAILS: NEED_COMPANY_FOR_TRUCK_CREATION}, status=status.HTTP_400_BAD_REQUEST)

            user = self.request.user
            if getattr(user, "role_type", None) != "owner" or _user_company_id(user) != company.id:
                logging.error("[truck_viewset - perform_create] Solo los dueños pueden crear camiones para su propia empresa.")
                return Response({DETAILS: ONLY_OWNERS_CAN_CREATE_TRUCKS}, status=status.HTTP_400_BAD_REQUEST)

            if driver and hasattr(driver, "truck"):
                old_truck = getattr(driver, "truck", None)
                if old_truck:
                    logging.info(f"[truck_viewset - perform_create] Liberando camión previo {old_truck.id} del conductor {driver.id}")
                    old_truck.driver = None
                    old_truck.save(update_fields=["driver"])

            truck = serializer.save()

            logging.info(f"[truck_viewset - perform_create] Camión {truck.registration_number} creado correctamente (empresa {company.id}, conductor {driver.id if driver else 'sin asignar'})")
            return truck

        except Exception as e:
            logging.error(f"[truck_viewset - perform_create] Error creando camión: {str(e)}")
            return Response({DETAILS: {ERROR_CREATING_TRUCK: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_update(self, serializer):
        try:
            instance = self.get_object()
            new_company = serializer.validated_data.get("company", instance.company)

            user = self.request.user
            if not (user.is_staff or user.is_superuser):
                if getattr(user, "role_type", None) != "owner" or _user_company_id(user) != new_company.id:
                    logging.error("[truck_viewset - perform_update] Solo puedes actualizar camiones de tu empresa.")
                    return Response({DETAILS: ONLY_UPDATE_TRUCKS_SAME_COMPANY}, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
        except Exception as e:
            logging.error(f"[truck_viewset - perform_update] Error actualizando camión: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=["post"], url_path=r"assign-driver/(?P<worker_id>\d+)")
    def assign_driver(self, request, worker_id=None):
        try:
            logging.info(f"[truck_viewset - assign_driver] Asignando conductor {worker_id} a camión por usuario {request.user.id}")
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            truck_id = serializer.validated_data["truck_id"]
            force = serializer.validated_data["force"]

            truck = Truck.objects.get(id=truck_id)
            worker = Worker.objects.get(id=worker_id)

            validate = self._validate_driver_same_company(company=truck.company, driver=worker)
            if not validate:
                return Response({DETAILS: {DRIVER_TRUCK_SAME_COMPANY}}, status=status.HTTP_400_BAD_REQUEST)

            if truck.driver_id and not force:
                return Response({DETAILS: {ALREADY_HAVE_DRIVER}}, status=status.HTTP_400_BAD_REQUEST)

            previous_truck = Truck.objects.filter(driver=worker).first()
            if previous_truck and previous_truck != truck:
                previous_truck.driver = None
                previous_truck.save(update_fields=["driver"])

            truck.driver = worker
            truck.save(update_fields=["driver"])

            logging.info(f"[truck_viewset - assign_driver] Conductor {worker_id} asignado a camión {truck_id} por usuario {request.user.id}")
            return Response(TruckSerializer(truck).data, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[truck_viewset - assign_driver] Error asignando conductor: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

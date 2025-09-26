# apps/truck/api/viewsets/truck_viewset.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import FilterSet, CharFilter, NumberFilter, DjangoFilterBackend
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser
from apps.truck.models import Truck
from apps.truck.api.serializers.truck_serializers import (
    TruckSerializer,
    CreateTruckSerializer,
    UpdateTruckSerializer,
    PartialUpdateTruckSerializer,
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_TRUCK,
    ONLY_OWNERS_CAN_CREATE_TRUCKS,
    NEED_COMPANY_FOR_TRUCK_CREATION,
    DRIVER_TRUCK_SAME_COMPANY,
    ONLY_UPDATE_TRUCKS_SAME_COMPANY
)
import logging

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


def _driver_company_id(user_driver):
    return getattr(getattr(user_driver, "worker_profile", None), "company_id", None)


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
            return
        drv_company_id = _driver_company_id(driver)
        if drv_company_id is None or company is None or drv_company_id != company.id:
            logging.error("El conductor debe pertenecer a la misma empresa que el camión.")
            raise ValueError(DRIVER_TRUCK_SAME_COMPANY)

    def perform_create(self, serializer):
        try:
            company = serializer.validated_data.get("company")
            driver = serializer.validated_data.get("driver")

            if not company:
                logging.error("Debe especificar la empresa (company) para crear un camión.")
                raise ValueError(NEED_COMPANY_FOR_TRUCK_CREATION)

            user = self.request.user
            if getattr(user, "role_type", None) != "owner" or _user_company_id(user) != company.id:
                logging.error("Solo los dueños pueden crear camiones para su propia empresa.")
                raise ValueError(ONLY_OWNERS_CAN_CREATE_TRUCKS)

            self._validate_driver_same_company(company=company, driver=driver)

            serializer.save()
        except Exception as e:
            logging.error(f"Error creando camión: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_TRUCK} - {str(e)}")

    def perform_update(self, serializer):
        try:
            instance = self.get_object()
            new_company = serializer.validated_data.get("company", instance.company)
            new_driver = serializer.validated_data.get("driver", instance.driver)

            self._validate_driver_same_company(company=new_company, driver=new_driver)

            user = self.request.user
            if not (user.is_staff or user.is_superuser):
                if getattr(user, "role_type", None) != "owner" or _user_company_id(user) != new_company.id:
                    logging.error("Solo puedes actualizar camiones de tu empresa.")
                    raise ValueError(ONLY_UPDATE_TRUCKS_SAME_COMPANY)

            serializer.save()
        except Exception as e:
            logging.error(f"Error actualizando camión: {str(e)}")
            raise Exception(f"{ERROR}: {str(e)}")

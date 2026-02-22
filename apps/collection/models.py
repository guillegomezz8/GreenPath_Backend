from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.enums import ContainerType, CollectionStatus, DeductionReason, CollectionRequestStatus, PlannedSource
from apps.user.models.client import Client
from apps.user.models.worker import Worker
from apps.route.models import RouteDayClient
from apps.base.enums import CollectionStatus, DeductionReason
from apps.collection.utils import container_capacity_liters


class Collection(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="collections",
        verbose_name="Cliente",
    )

    route_day_client = models.ForeignKey(
        RouteDayClient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collections",
        verbose_name="Parada planificada",
    )

    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collections",
        verbose_name="Trabajador",
    )

    collection_date = models.DateField("Fecha de Recogida")

    container_type = models.CharField(
        "Tipo de Envase",
        max_length=10,
        choices=ContainerType.choices,
        default=ContainerType.BIDONES,
    )

    container_number = models.PositiveIntegerField(
        "Número de Envases",
        validators=[MinValueValidator(1)],
        default=1,
    )

    estimated_liters = models.DecimalField(
        "Litros estimados",
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )

    measured_liters = models.DecimalField(
        "Litros medidos (brutos)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        null=True,
        blank=True,
    )

    deduction_liters = models.DecimalField(
        "Litros descontados",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )

    deduction_reason = models.CharField(
        "Motivo descuento",
        max_length=20,
        choices=DeductionReason.choices,
        default=DeductionReason.RESIDUE,
    )

    deduction_notes = models.TextField("Notas descuento", blank=True, default="")

    net_liters = models.DecimalField(
        "Litros netos (facturables)",
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )

    price_per_liter = models.DecimalField(
        "Precio por Litro",
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.00"))],
        default=Decimal("0.00"),
    )

    total_price = models.DecimalField(
        "Precio Total",
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )

    status = models.CharField(
        "Estado",
        max_length=30,
        choices=CollectionStatus.choices,
        default=CollectionStatus.PENDING_MEASUREMENT,
    )

    notes = models.TextField("Notas", blank=True, default="")

    class Meta:
        verbose_name = "Recogida"
        verbose_name_plural = "Recogidas"
        constraints = [
            models.UniqueConstraint(
                fields=["route_day_client"],
                condition=Q(route_day_client__isnull=False) & ~Q(status=CollectionStatus.CANCELED),
                name="uniq_active_collection_per_route_day_client",
            )
        ]

    @property
    def is_manual(self) -> bool:
        return self.route_day_client_id is None

    @property
    def route(self):
        if not self.route_day_client_id:
            return None
        return self.route_day_client.route_day.route

    def clean(self):
        if self.route_day_client_id:
            route_day_client = self.route_day_client
            if self.client_id != route_day_client.client_id:
                raise ValueError("El cliente no coincide con la parada planificada.")
            if self.collection_date != route_day_client.route_day.date:
                raise ValueError("La fecha no coincide con la ruta diaria planificada.")

        if self.measured_liters is not None and self.deduction_liters > self.measured_liters:
            raise ValueError("Los litros descontados no pueden ser mayores que los litros medidos.")

        if self.status == CollectionStatus.CONFIRMED and self.measured_liters is None:
            raise ValueError("Para confirmar la recogida debes indicar los litros medidos.")

    def save(self, *args, **kwargs):

        self.full_clean()

        capacity = container_capacity_liters(self.container_type)
        self.estimated_liters = (Decimal(self.container_number) * capacity).quantize(Decimal("0.01"))

        measured = self.measured_liters if self.measured_liters is not None else self.estimated_liters
        deduction = self.deduction_liters or Decimal("0.00")
        if deduction > measured:
            deduction = measured

        self.net_liters = (measured - deduction).quantize(Decimal("0.01"))
        self.total_price = (self.net_liters * (self.price_per_liter or Decimal("0.00"))).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recogida #{self.id} - {self.client.name} - {self.collection_date.strftime('%Y-%m-%d')}"
    

class CollectionRequest(BaseModel):
    route_day_client = models.OneToOneField(
        RouteDayClient,
        on_delete=models.CASCADE,
        related_name="collection_request",
        verbose_name="Parada planificada",
    )

    expires_at = models.DateTimeField("Expira en")

    status = models.CharField(
        "Estado",
        max_length=20,
        choices=CollectionRequestStatus.choices,
        default=CollectionRequestStatus.PENDING,
    )

    container_type = models.CharField(
        "Tipo de envase",
        max_length=10,
        choices=ContainerType.choices,
        default=ContainerType.BIDONES,
    )
    container_number = models.PositiveIntegerField("Número de envases", null=True, blank=True)

    estimated_liters = models.DecimalField("Litros estimados", max_digits=10, decimal_places=2, null=True, blank=True)

    final_liters = models.DecimalField("Litros finales", max_digits=10, decimal_places=2, null=True, blank=True)
    final_source = models.CharField("Fuente final", max_length=10, choices=PlannedSource.choices, null=True, blank=True)

    class Meta:
        verbose_name = "Solicitud de Recogida"
        verbose_name_plural = "Solicitudes de Recogida"

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def compute_client_liters(self) -> Decimal | None:
        if not self.container_number:
            return None
        capacity = container_capacity_liters(self.container_type)
        return (Decimal(self.container_number) * capacity).quantize(Decimal("0.01"))
    
    def __str__(self):
        return f"Solicitud de Recogida - {self.route_day_client.client.name} - {self.route_day_client.route_day.date.strftime('%Y-%m-%d')}"
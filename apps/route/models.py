from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils.formats import date_format

from apps.company.models import Company
from apps.base.enums import Weekday, RouteDayStatus
from apps.zone.models import Zone
from apps.user.models.worker import Worker
from apps.base.models import BaseModel
from apps.user.models.client import Client


class Route(BaseModel):
    name = models.CharField(
        'Nombre de la Ruta',
        max_length=100,
        unique=True
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name='Compania'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        related_name='routes',
        verbose_name='Trabajador',
        null=True,
        blank=True,
    )
    start_date = models.DateField('Fecha de Inicio')
    end_date = models.DateField('Fecha de Fin', null=True, blank=True)
    week_start = models.IntegerField(
        'Día de Inicio de la Semana',
        default=0,
        choices=Weekday.choices
    )
    week_end = models.IntegerField(
        'Día de Fin de la Semana',
        default=6,
        choices=Weekday.choices
    )

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'

    def __str__(self):
        start_day = Weekday(self.week_start).label
        end_day = Weekday(self.week_end).label
        return f'{self.name} - {start_day} a {end_day}'


class RouteDay(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="route_days",
        verbose_name="Ruta",
    )

    date = models.DateField("Fecha de la Ruta")

    status = models.CharField(
        "Estado",
        max_length=20,
        choices=RouteDayStatus.choices,
        default=RouteDayStatus.PLANNED,
    )
    
    daily_capacity_liters = models.DecimalField(
        "Capacidad Diaria (litros)",
        max_digits=10,
        decimal_places=2, 
        null=True, 
        blank=True
    )

    started_at = models.DateTimeField(
        "Inicio",
        null=True,
        blank=True,
    )

    finished_at = models.DateTimeField(
        "Fin",
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = ("route", "date")
        ordering = ["date"]
        verbose_name = "Ruta Diaria"
        verbose_name_plural = "Rutas Diarias"

    @property
    def weekday(self) -> int:
        return self.date.weekday()

    @property
    def display_name(self) -> str:
        return f"{self.route.name} - {date_format(self.date, 'd/m/Y')}"

    def __str__(self):
        return self.display_name

    def admin_link(self):
        url = reverse("admin:route_routeday_change", args=[self.id])
        return format_html('<a href="{}">Editar</a>', url)
    
    admin_link.short_description = "Editar Día"


class RouteDayClient(models.Model):
    route_day = models.ForeignKey(
        RouteDay,
        on_delete=models.CASCADE,
        related_name="ordered_clients",
        verbose_name="Ruta Diaria",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name="Cliente",
    )
    order = models.PositiveIntegerField("Orden de Recogida")

    class Meta:
        ordering = ["order"]
        verbose_name = "Cliente en Ruta Diaria"
        verbose_name_plural = "Clientes en Ruta Diaria"
        constraints = [
            models.UniqueConstraint(fields=["route_day", "order"], name="uniq_route_day_order"),
            models.UniqueConstraint(fields=["route_day", "client"], name="uniq_route_day_client"),
        ]

    def __str__(self):
        return f"{self.client.name} - Orden {self.order}"


class RouteZoneDay(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='zone_days',
        verbose_name='Ruta'
    )
    weekday = models.IntegerField(
        'Día de la Semana',
        choices=Weekday.choices
    )
    zones = models.ManyToManyField(
        Zone,
        related_name='route_zone_days',
        verbose_name='Zonas asignadas'
    )

    class Meta:
        unique_together = ('route', 'weekday')
        verbose_name = 'Zona por Día de Ruta'
        verbose_name_plural = 'Zonas por Día de Ruta'

    def __str__(self):
        day_name = Weekday(self.weekday).label
        zones_qs = self.zones.all()
        zones_str = ", ".join([z.name for z in zones_qs]) if zones_qs.exists() else "Sin zonas"
        return f"{self.route.name} - {day_name}: {zones_str}"

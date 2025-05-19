from django.db import models
from apps.company.models import Company
from apps.base.enums import Weekday, RouteFrequency
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
        verbose_name='Compañía'
    )
    workers = models.ManyToManyField(
        Worker,
        related_name='routes',
        verbose_name='Trabajadores'
    )
    frequency = models.CharField(
        'Frecuencia',
        max_length=10,
        choices=RouteFrequency.choices,
        default=RouteFrequency.WEEKLY
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
        related_name='route_days',
        verbose_name='Ruta'
    )
    date = models.DateField('Fecha de la Ruta')
    name = models.CharField('Nombre Ruta Diaria', max_length=255, blank=True)
    date_generated = models.DateField('Fecha de Generación', auto_now_add=True)

    class Meta:
        unique_together = ('route', 'date')
        ordering = ['date']
        verbose_name = 'Ruta Diaria'
        verbose_name_plural = 'Rutas Diarias'

    def __str__(self):
        return f'{self.route.name} - {self.date.strftime("%A %d/%m/%Y")}'


class RouteDayClient(models.Model):
    route_day = models.ForeignKey(
        RouteDay,
        on_delete=models.CASCADE,
        related_name='ordered_clients',
        verbose_name='Ruta Diaria'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        verbose_name='Cliente'
    )
    order = models.PositiveIntegerField('Orden de Recogida')

    class Meta:
        unique_together = ('route_day', 'order')
        ordering = ['order']
        verbose_name = 'Cliente en Ruta Diaria'
        verbose_name_plural = 'Clientes en Ruta Diaria'

    def __str__(self):
        return f'{self.client.name} - Orden {self.order}'

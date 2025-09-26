from django.db import models
from apps.base.models import BaseModel
from apps.user.models.worker import Worker
from apps.base.enums import TruckStatus, Fuel


class Truck(BaseModel):
    registration_number = models.CharField('Matrícula', max_length=255)
    brand = models.CharField('Marca', max_length=64, blank=True, null=True)
    model = models.CharField('Modelo', max_length=255, blank=True, null=True)
    year = models.IntegerField('Año', blank=True, null=True)
    capacity = models.DecimalField('Capacidad', max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField('Estado', max_length=20, choices=TruckStatus.choices, default=TruckStatus.ACTIVE)
    fuel = models.CharField('Combustible', max_length=20, choices=Fuel.choices, blank=True, null=True)

    driver = models.OneToOneField(
        Worker,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='truck',
        verbose_name='Conductor'
    )

    company = models.ForeignKey(
        'company.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trucks',
        verbose_name='Empresa'
    )

    class Meta:
        verbose_name = 'Camión'
        verbose_name_plural = 'Camiones'

    def __str__(self):
        return self.registration_number

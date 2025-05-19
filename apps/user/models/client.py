from django.db import models
from apps.user.models.user import User
from apps.company.models import Company
from apps.base.models import BaseModel
from apps.base.enums import Weekday, PickupFrequency


class Client(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Usuario'
    )
    companies = models.ManyToManyField(
        Company,
        related_name='clients',
        blank=True,
        verbose_name='Empresa'
    )
    name = models.CharField(
        max_length=255,
        blank=True
    )
    phone = models.CharField(
        'Teléfono', 
        max_length=20, 
        blank=True
    )
    cif = models.CharField(
        'CIF', 
        max_length=20, 
        blank=True
    )
    address = models.CharField(
        'Dirección', 
        max_length=255, 
        blank=True
    )
    city = models.CharField(
        'Ciudad', 
        max_length=100, 
        blank=True
    )
    postal_code = models.CharField(
        'Código Postal', 
        max_length=10, 
        blank=True
    )
    country = models.CharField(
        'País', 
        max_length=100, 
        default='España', 
        blank=True
    )
    latitude = models.DecimalField('Latitud', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Longitud', max_digits=9, decimal_places=6, null=True, blank=True)


    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.name} - Cliente'


class ClientPickupSchedule(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='pickup_schedules'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='pickup_schedules'
    )
    weekday = models.IntegerField(
        'Día de la Semana',
        choices=Weekday.choices
    )
    frequency = models.CharField(
        'Frecuencia',
        max_length=10,
        choices=PickupFrequency.choices,
        default=PickupFrequency.WEEKLY
    )


    class Meta:
        verbose_name = 'Horario de Recogida de Cliente'
        verbose_name_plural = 'Horarios de Recogida de Clientes'

    def __str__(self):
        return f'{self.client.name} - {self.get_weekday_display()} - {self.get_frequency_display()}'
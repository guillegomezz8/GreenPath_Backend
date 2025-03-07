from django.db import models
from apps.user.models.user import User
from apps.company.models import Company
from apps.base.models import BaseModel

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
    adress = models.CharField(
        max_length=255,
        blank=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True
    )
    cif = models.CharField(
        max_length=255,
        blank=True
    )

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.name} - Cliente'

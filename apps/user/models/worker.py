from django.db import models
from apps.user.models.user import User
from apps.company.models import Company
from apps.base.enums import Role
from apps.base.models import BaseModel

class Worker(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='worker_profile',
        verbose_name='Usuario'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Empresa',
        related_name='workers'
    )
    role = models.CharField(
        'Rol',
        max_length=10,
        choices=Role.choices,
        default=Role.WORKER
    )
    name = models.CharField(
        'Nombre',
        max_length=255,
        blank=True
    )
    surname = models.CharField(
        'Apellidos',
        max_length=255,
        blank=True
    )
    address = models.CharField(
        'Dirección',
        max_length=255,
        blank=True
    )
    phone = models.CharField(
        'Teléfono',
        max_length=20,
        blank=True
    )
    dni = models.CharField(
        'DNI',
        max_length=255,
        blank=True
    )
    photo = models.ImageField(
        'Foto',
        upload_to='workers/',
        null=True,
        blank=True
    )
    birth_date = models.DateField(
        'Fecha de Nacimiento',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'

    def __str__(self):
        return f'{self.name} - {self.get_role_display()}'

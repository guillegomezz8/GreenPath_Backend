from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as geomodels

import logging

from apps.base.models import BaseModel
from apps.user.models.user import User
from apps.base.enums import Role
from apps.base.logger import configure_logging

configure_logging()


class Company(BaseModel):
    name = models.CharField('Nombre', max_length=255)
    address = models.CharField('Dirección', max_length=255, blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email = models.EmailField('Email', max_length=255, blank=True, null=True)
    cif = models.CharField('CIF', max_length=20, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='logo/', max_length=255, null=True, blank=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name='Dueño'
    )

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.name

    def clean(self):
        logging.info("Validando que el dueño es un owner")
        if self.owner and self.owner.role_type and self.owner.role_type != Role.OWNER:
            logging.error("El dueño no tiene el rol de owners")
            raise ValidationError({'owner': 'El dueño debe tener el rol de "owner".'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CompanyHub(BaseModel):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="hub",
        verbose_name="Empresa",
    )

    name = geomodels.CharField('Nombre del Hub', max_length=255)
    location = geomodels.PointField('Ubicación', geography=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Hub de Empresa'
        verbose_name_plural = 'Hubs de Empresas'

    def __str__(self):
        return f"{self.name} - {self.company.name}"
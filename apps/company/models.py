from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as geomodels
from django.core.validators import MinValueValidator
from decimal import Decimal

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
        logging.info("[company_model - CompanyModel] Validando que el dueño es un owner")
        if self.owner and self.owner.role_type and self.owner.role_type != Role.OWNER:
            logging.error("[company_model - CompanyModel] El dueño no tiene el rol de owners")
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


class CompanySettings(BaseModel):
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name="Empresa",
    )

    default_price_per_liter = models.DecimalField(
        "Precio global por litro",
        max_digits=7,
        decimal_places=3,
        default=Decimal("1.200"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    billing_business_name = models.CharField("Razon social", max_length=255, blank=True, default="")
    billing_tax_id = models.CharField("CIF", max_length=20, blank=True, default="")
    billing_address = models.CharField("Direccion fiscal", max_length=255, blank=True, default="")
    billing_postal_code = models.CharField("Codigo postal", max_length=10, blank=True, default="")
    billing_city = models.CharField("Ciudad", max_length=100, blank=True, default="")
    billing_province = models.CharField("Provincia", max_length=100, blank=True, default="")
    billing_country = models.CharField("Pais", max_length=100, blank=True, default="Espana")
    billing_phone = models.CharField("Telefono", max_length=20, blank=True, default="")
    billing_email = models.EmailField("Email", blank=True, default="")
    billing_bank_account = models.CharField("Cuenta bancaria", max_length=64, blank=True, default="")
    billing_logo = models.ImageField("Logo facturacion", upload_to="company/billing/", max_length=255, blank=True, null=True)
    billing_ler_code = models.CharField("Codigo LER", max_length=50, blank=True, default="")
    billing_footer = models.TextField("Pie de factura", blank=True, default="")

    class Meta:
        verbose_name = "Configuracion de Empresa"
        verbose_name_plural = "Configuraciones de Empresa"

    def __str__(self):
        return f"Configuracion - {self.company.name}"

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.base.enums import BulkCollectionCalculationMode, QuantityUnit
from apps.base.models import BaseModel
from apps.base.literals import BULK_COLLECTION_CLIENT_INVALID, BULK_COLLECTION_INTEGER_UNITS_REQUIRED, BULK_COLLECTION_POSITIVE_VALUE_REQUIRED
from apps.company.models import Company
from apps.user.models.client import Client


MONEY_STEP = Decimal("0.01")
UNIT_PRICE_STEP = Decimal("0.0001")
QUANTITY_STEP = Decimal("0.01")


class BulkCollection(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="bulk_collections",
        verbose_name="Empresa",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="bulk_collections",
        verbose_name="Cliente",
    )
    collection_date = models.DateField("Fecha de recogida")
    invoice_file = models.FileField(
        "Factura adjunta",
        upload_to="bulk_collections/invoices/",
        blank=True,
        null=True,
    )
    unit = models.CharField("Unidad", max_length=2, choices=QuantityUnit.choices)
    calculation_mode = models.CharField(
        "Valor calculado",
        max_length=20,
        choices=BulkCollectionCalculationMode.choices,
        default=BulkCollectionCalculationMode.TOTAL,
    )
    quantity = models.DecimalField(
        "Cantidad",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        "Precio unitario",
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    total_price = models.DecimalField(
        "Importe final",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    billable = models.BooleanField("Facturable", default=True)
    notes = models.TextField("Observaciones", blank=True, default="")

    class Meta:
        verbose_name = "Recogida al por mayor"
        verbose_name_plural = "Recogidas al por mayor"
        ordering = ("-collection_date", "-id")
        indexes = [
            models.Index(fields=["company", "collection_date"], name="bulk_company_date_idx"),
            models.Index(fields=["company", "billable"], name="bulk_company_bill_idx"),
        ]

    def clean(self):
        super().clean()
        if self.company_id and self.client_id and not self.client.companies.filter(id=self.company_id).exists():
            raise ValidationError({"client": BULK_COLLECTION_CLIENT_INVALID})

        for field_name in ("quantity", "unit_price", "total_price"):
            value = getattr(self, field_name, None)
            if value is None or value <= 0:
                raise ValidationError({field_name: BULK_COLLECTION_POSITIVE_VALUE_REQUIRED})
        if self.unit == QuantityUnit.UNIT and self.quantity % 1 != 0:
            raise ValidationError({"quantity": BULK_COLLECTION_INTEGER_UNITS_REQUIRED})

    def calculate_missing_value(self):
        if self.calculation_mode == BulkCollectionCalculationMode.TOTAL:
            self.total_price = (self.quantity * self.unit_price).quantize(MONEY_STEP, rounding=ROUND_HALF_UP)
        elif self.calculation_mode == BulkCollectionCalculationMode.UNIT_PRICE:
            self.unit_price = (self.total_price / self.quantity).quantize(UNIT_PRICE_STEP, rounding=ROUND_HALF_UP)
        elif self.calculation_mode == BulkCollectionCalculationMode.QUANTITY:
            self.quantity = (self.total_price / self.unit_price).quantize(QUANTITY_STEP, rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        self.calculate_missing_value()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        total = self.total_price or Decimal("0.00")
        return f"Recogida #{self.pk or '-'} - {self.client} - {total:.2f} EUR"

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.base.models import BaseModel
from apps.company.models import Company


class Buyer(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="buyers",
        verbose_name="Empresa",
    )
    fiscal_name = models.CharField("Razon social", max_length=255)
    tax_id = models.CharField("CIF / NIF", max_length=20)
    fiscal_address = models.CharField("Direccion fiscal", max_length=255)
    postal_code = models.CharField("Codigo postal", max_length=10)
    city = models.CharField("Ciudad", max_length=100)
    province = models.CharField("Provincia", max_length=100)
    country = models.CharField("Pais", max_length=100, default="Espana", blank=True)
    email = models.EmailField("Email", blank=True, default="")
    phone = models.CharField("Telefono", max_length=20, blank=True, default="")
    contact_person = models.CharField("Persona de contacto", max_length=255, blank=True, default="")
    notes = models.TextField("Observaciones", blank=True, default="")

    class Meta:
        verbose_name = "Comprador"
        verbose_name_plural = "Compradores"
        constraints = [
            models.UniqueConstraint(fields=["company", "tax_id"], name="uniq_buyer_tax_id_per_company"),
        ]
        ordering = ("fiscal_name",)

    @property
    def full_fiscal_address(self):
        parts = [self.fiscal_address]
        locality = " ".join([value for value in [self.postal_code, self.city, self.province] if value])
        if locality:
            parts.append(locality)
        if self.country:
            parts.append(self.country)
        return ", ".join([value for value in parts if value])

    def __str__(self):
        return f"{self.fiscal_name} - {self.tax_id}"


class Sale(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="sales",
        verbose_name="Empresa",
    )
    buyer = models.ForeignKey(
        Buyer,
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name="Comprador",
    )
    sale_date = models.DateField("Fecha de venta")
    invoice_date = models.DateField("Fecha de factura", blank=True, null=True)
    product_description = models.TextField("Producto / descripcion")
    quantity = models.DecimalField(
        "Cantidad",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit = models.CharField("Unidad", max_length=20, default="L")
    unit_price = models.DecimalField(
        "Precio unitario",
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal = models.DecimalField("Base imponible", max_digits=12, decimal_places=2, editable=False, default=Decimal("0.00"))
    tax_rate = models.DecimalField(
        "IVA %",
        max_digits=5,
        decimal_places=2,
        default=Decimal("21.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tax_amount = models.DecimalField("Importe IVA", max_digits=12, decimal_places=2, editable=False, default=Decimal("0.00"))
    total = models.DecimalField("Total", max_digits=12, decimal_places=2, editable=False, default=Decimal("0.00"))
    currency = models.CharField("Moneda", max_length=10, default="EUR")
    invoice_year = models.PositiveIntegerField("Ano factura", blank=True, null=True, editable=False)
    invoice_sequence = models.PositiveIntegerField("Secuencia factura", blank=True, null=True, editable=False)
    invoice_number = models.CharField("Numero de factura", max_length=20, blank=True, default="", editable=False)
    invoice_pdf = models.FileField("Factura PDF", upload_to="sales/invoices/", blank=True, null=True)
    invoice_generated_at = models.DateTimeField("Factura generada en", blank=True, null=True)
    notes = models.TextField("Observaciones", blank=True, default="")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        constraints = [
            models.UniqueConstraint(fields=["company", "invoice_year", "invoice_sequence"], name="uniq_sale_invoice_sequence"),
            models.UniqueConstraint(fields=["company", "invoice_number"], name="uniq_sale_invoice_number"),
        ]
        ordering = ("-invoice_date", "-id")

    def clean(self):
        if self.buyer_id and self.company_id and self.buyer.company_id != self.company_id:
            raise ValueError("El comprador no pertenece a la misma empresa que la venta.")

    def save(self, *args, **kwargs):
        if self.invoice_date:
            self.sale_date = self.invoice_date
            self.invoice_year = self.invoice_date.year
            self.invoice_sequence = None
        if not self.invoice_date:
            self.invoice_date = self.sale_date

        self.subtotal = (Decimal(self.quantity or Decimal("0.00")) * Decimal(self.unit_price or Decimal("0.00"))).quantize(Decimal("0.01"))
        self.tax_amount = (self.subtotal * (Decimal(self.tax_rate or Decimal("0.00")) / Decimal("100"))).quantize(Decimal("0.01"))
        self.total = (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))

        self.full_clean()
        super().save(*args, **kwargs)

    def recalculate_from_lines(self):
        lines = list(self.lines.order_by("position", "id"))
        if not lines:
            return

        subtotal = sum((line.subtotal for line in lines), Decimal("0.00"))
        tax_amount = sum((line.tax_amount for line in lines), Decimal("0.00"))
        quantity = sum((line.quantity for line in lines), Decimal("0.00"))
        units = {line.unit for line in lines}
        tax_rates = {line.tax_rate for line in lines}

        self.product_description = "\n".join(line.product_description for line in lines)
        self.quantity = quantity
        self.unit = units.pop() if len(units) == 1 else "varias"
        self.unit_price = (
            (subtotal / quantity).quantize(Decimal("0.0001"))
            if quantity
            else Decimal("0.0000")
        )
        self.tax_rate = tax_rates.pop() if len(tax_rates) == 1 else Decimal("0.00")
        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.tax_amount = tax_amount.quantize(Decimal("0.01"))
        self.total = (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))
        self.full_clean()
        super().save(
            update_fields=(
                "product_description",
                "quantity",
                "unit",
                "unit_price",
                "tax_rate",
                "subtotal",
                "tax_amount",
                "total",
                "modified_date",
            )
        )

    def __str__(self):
        return self.invoice_number or f"Venta #{self.id}"


class SaleLine(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name="Venta",
    )
    position = models.PositiveIntegerField("Posicion", default=0)
    product_description = models.TextField("Producto / descripcion")
    quantity = models.DecimalField(
        "Cantidad",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit = models.CharField("Unidad", max_length=20, default="L")
    unit_price = models.DecimalField(
        "Precio unitario",
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    tax_rate = models.DecimalField(
        "IVA %",
        max_digits=5,
        decimal_places=2,
        default=Decimal("21.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    subtotal = models.DecimalField(
        "Base imponible",
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )
    tax_amount = models.DecimalField(
        "Importe IVA",
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        "Total",
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=Decimal("0.00"),
    )

    class Meta:
        verbose_name = "Linea de venta"
        verbose_name_plural = "Lineas de venta"
        ordering = ("position", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["sale", "position"],
                name="uniq_sale_line_position",
            ),
        ]

    def calculate_totals(self):
        self.subtotal = (
            Decimal(self.quantity or Decimal("0.00"))
            * Decimal(self.unit_price or Decimal("0.00"))
        ).quantize(Decimal("0.01"))
        self.tax_amount = (
            self.subtotal
            * (Decimal(self.tax_rate or Decimal("0.00")) / Decimal("100"))
        ).quantize(Decimal("0.01"))
        self.total = (self.subtotal + self.tax_amount).quantize(Decimal("0.01"))

    def save(self, *args, recalculate_sale=True, **kwargs):
        self.calculate_totals()
        self.full_clean()
        super().save(*args, **kwargs)
        if recalculate_sale:
            self.sale.recalculate_from_lines()

    def delete(self, *args, **kwargs):
        sale = self.sale
        result = super().delete(*args, **kwargs)
        if Sale.objects.filter(pk=sale.pk).exists():
            sale.recalculate_from_lines()
        return result

    def __str__(self):
        return f"{self.sale} - linea {self.position + 1}"

import hashlib
import json
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.base.models import BaseModel
from apps.company.models import Company, CompanySettings


class SaleInvoiceIssuerSnapshot(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="sale_invoice_issuer_snapshots",
        verbose_name="Empresa",
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
    billing_logo = models.ImageField("Logo facturacion", upload_to="sale/issuer_snapshots/", max_length=255, blank=True, null=True)
    billing_ler_code = models.CharField("Codigo LER", max_length=50, blank=True, default="")
    billing_footer = models.TextField("Pie de factura", blank=True, default="")
    data_hash = models.CharField("Hash de datos", max_length=64, db_index=True, editable=False)
    created_date = models.DateTimeField("Fecha de creacion", auto_now_add=True)

    BILLING_FIELDS = (
        "billing_business_name",
        "billing_tax_id",
        "billing_address",
        "billing_postal_code",
        "billing_city",
        "billing_province",
        "billing_country",
        "billing_phone",
        "billing_email",
        "billing_bank_account",
        "billing_logo",
        "billing_ler_code",
        "billing_footer",
    )

    class Meta:
        verbose_name = "Datos fiscales de factura"
        verbose_name_plural = "Datos fiscales de facturas"
        ordering = ("-created_date", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=["company", "data_hash"],
                name="uniq_sale_invoice_snapshot_company_hash",
            ),
        ]

    @classmethod
    def _file_name(cls, file_field):
        return getattr(file_field, "name", "") or ""

    @classmethod
    def _hash_data(cls, data):
        normalized = {
            field: str(data.get(field) or "")
            for field in cls.BILLING_FIELDS
        }
        raw = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def current_data_for_company(cls, company):
        settings_obj, _ = CompanySettings.objects.get_or_create(company=company)
        return {
            "billing_business_name": settings_obj.billing_business_name or company.name or "",
            "billing_tax_id": settings_obj.billing_tax_id or company.cif or "",
            "billing_address": settings_obj.billing_address or company.address or "",
            "billing_postal_code": settings_obj.billing_postal_code or "",
            "billing_city": settings_obj.billing_city or "",
            "billing_province": settings_obj.billing_province or "",
            "billing_country": settings_obj.billing_country or "Espana",
            "billing_phone": settings_obj.billing_phone or company.phone or "",
            "billing_email": settings_obj.billing_email or company.email or "",
            "billing_bank_account": settings_obj.billing_bank_account or "",
            "billing_logo": cls._file_name(settings_obj.billing_logo) or cls._file_name(company.logo),
            "billing_ler_code": settings_obj.billing_ler_code or "",
            "billing_footer": settings_obj.billing_footer or "",
        }

    @classmethod
    def get_or_create_for_company(cls, company):
        data = cls.current_data_for_company(company)
        data_hash = cls._hash_data(data)
        snapshot, _ = cls.objects.get_or_create(
            company=company,
            data_hash=data_hash,
            defaults=data,
        )
        return snapshot

    def _value_for_hash(self, field):
        if field == "billing_logo":
            return self._file_name(self.billing_logo)
        return getattr(self, field)

    def save(self, *args, **kwargs):
        data = {
            field: self._value_for_hash(field)
            for field in self.BILLING_FIELDS
        }
        self.data_hash = self._hash_data(data)
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"data_hash"}
        super().save(*args, **kwargs)

    def __str__(self):
        name = self.billing_business_name or self.company.name
        return f"{name} - {self.billing_bank_account or 'sin cuenta'}"


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
    invoice_issuer = models.ForeignKey(
        SaleInvoiceIssuerSnapshot,
        on_delete=models.PROTECT,
        related_name="sales",
        verbose_name="Datos fiscales de factura",
        blank=True,
        null=True,
        editable=True,
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
        if self.invoice_issuer_id and self.company_id and self.invoice_issuer.company_id != self.company_id:
            raise ValueError("Los datos fiscales no pertenecen a la empresa de la venta.")

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

        if self.company_id and not self.invoice_issuer_id:
            self.invoice_issuer = SaleInvoiceIssuerSnapshot.get_or_create_for_company(self.company)

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

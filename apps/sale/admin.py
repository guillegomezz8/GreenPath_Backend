from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from apps.sale.models import Buyer, Sale, SaleInvoiceIssuerSnapshot, SaleLine


class SaleAdminForm(forms.ModelForm):
    manual_invoice_number = forms.CharField(required=True, label="Numero de factura")

    class Meta:
        model = Sale
        exclude = ("sale_date",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manual_invoice_number"].initial = self.instance.invoice_number if self.instance and self.instance.pk else ""

    def clean_manual_invoice_number(self):
        invoice_number = (self.cleaned_data.get("manual_invoice_number") or "").strip()
        if not invoice_number:
            raise ValidationError("El numero de factura es obligatorio.")

        company = self.cleaned_data.get("company") or getattr(self.instance, "company", None)
        if company:
            queryset = Sale.objects.filter(company=company, invoice_number__iexact=invoice_number)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise ValidationError("Ya existe una venta con ese numero de factura en esta empresa.")

        return invoice_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.invoice_number = self.cleaned_data["manual_invoice_number"]
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SaleLineInline(admin.TabularInline):
    model = SaleLine
    extra = 0
    fields = (
        "position",
        "product_description",
        "quantity",
        "unit",
        "unit_price",
        "tax_rate",
        "subtotal",
        "tax_amount",
        "total",
    )
    readonly_fields = ("subtotal", "tax_amount", "total")


class SaleInvoiceIssuerSnapshotAdminForm(forms.ModelForm):
    class Meta:
        model = SaleInvoiceIssuerSnapshot
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get("company") or getattr(self.instance, "company", None)
        if not company:
            return cleaned_data

        data = {}
        for field in SaleInvoiceIssuerSnapshot.BILLING_FIELDS:
            value = cleaned_data.get(field, getattr(self.instance, field, ""))
            if field == "billing_logo":
                data[field] = SaleInvoiceIssuerSnapshot._file_name(value)
            else:
                data[field] = value or ""

        data_hash = SaleInvoiceIssuerSnapshot._hash_data(data)
        snapshots = SaleInvoiceIssuerSnapshot.objects.filter(company=company, data_hash=data_hash)
        if self.instance and self.instance.pk:
            snapshots = snapshots.exclude(pk=self.instance.pk)

        if snapshots.exists():
            raise ValidationError("Ya existe una foto fiscal con esos datos para esta empresa.")

        return cleaned_data


class SaleInvoiceIssuerSaleInline(admin.TabularInline):
    model = Sale
    fk_name = "invoice_issuer"
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name = "Factura asociada"
    verbose_name_plural = "Facturas asociadas"
    fields = ("invoice_link", "invoice_date", "buyer", "total", "currency")
    readonly_fields = fields
    ordering = ("-invoice_date", "-id")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("buyer", "company")

    @admin.display(description="Factura")
    def invoice_link(self, obj):
        url = reverse("admin:sale_sale_change", args=[obj.pk])
        label = obj.invoice_number or f"Venta #{obj.pk}"
        return format_html('<a href="{}">{}</a>', url, label)


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fiscal_name",
        "tax_id",
        "company",
        "city",
        "province",
        "contact_person",
        "email",
        "phone",
    )
    search_fields = ("fiscal_name", "tax_id", "city", "province", "email", "phone", "contact_person")
    list_filter = ("company", "city", "province", "country")
    autocomplete_fields = ("company",)
    ordering = ("fiscal_name",)
    readonly_fields = ("full_fiscal_address_display",)
    fieldsets = (
        ("Empresa y fiscal", {
            "fields": ("company", "fiscal_name", "tax_id"),
        }),
        ("Direccion", {
            "fields": ("fiscal_address", "postal_code", "city", "province", "country", "full_fiscal_address_display"),
        }),
        ("Contacto", {
            "fields": ("contact_person", "email", "phone"),
        }),
        ("Notas", {
            "fields": ("notes",),
        }),
    )

    @admin.display(description="Direccion fiscal completa")
    def full_fiscal_address_display(self, obj):
        return obj.full_fiscal_address


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    form = SaleAdminForm
    inlines = (SaleLineInline,)
    list_display = ("id", "invoice_number", "invoice_date", "buyer", "company", "total", "currency")
    search_fields = ("invoice_number", "buyer__fiscal_name", "buyer__tax_id", "product_description", "notes")
    list_filter = ("company", "invoice_date", "currency", "tax_rate")
    autocomplete_fields = ("company", "buyer")
    list_select_related = ("company", "buyer", "invoice_issuer")
    ordering = ("-invoice_date", "-id")
    date_hierarchy = "invoice_date"
    readonly_fields = ("invoice_issuer", "subtotal", "tax_amount", "total")
    fieldsets = (
        ("Factura", {
            "fields": ("company", "buyer", "manual_invoice_number", "invoice_date", "currency", "invoice_issuer"),
        }),
        ("Concepto", {
            "fields": ("product_description", "quantity", "unit", "unit_price", "tax_rate"),
        }),
        ("Totales calculados", {
            "fields": ("subtotal", "tax_amount", "total"),
        }),
        ("Estado", {
            "fields": ("disabled",),
        }),
        ("Notas", {
            "fields": ("notes",),
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sale = form.instance
        if sale.lines.exists():
            sale.recalculate_from_lines()
            return

        line = SaleLine(
            sale=sale,
            position=0,
            product_description=sale.product_description,
            quantity=sale.quantity,
            unit=sale.unit,
            unit_price=sale.unit_price,
            tax_rate=sale.tax_rate,
        )
        line.save()


@admin.register(SaleInvoiceIssuerSnapshot)
class SaleInvoiceIssuerSnapshotAdmin(admin.ModelAdmin):
    form = SaleInvoiceIssuerSnapshotAdminForm
    inlines = (SaleInvoiceIssuerSaleInline,)
    list_display = (
        "id",
        "company",
        "billing_business_name",
        "billing_tax_id",
        "billing_bank_account",
        "created_date",
    )
    search_fields = (
        "company__name",
        "billing_business_name",
        "billing_tax_id",
        "billing_bank_account",
        "billing_email",
    )
    list_filter = ("company", "created_date")
    autocomplete_fields = ("company",)
    ordering = ("-created_date", "-id")
    readonly_fields = ("company", "data_hash", "created_date")
    fieldsets = (
        ("Empresa", {
            "fields": ("company", "billing_business_name", "billing_tax_id"),
        }),
        ("Direccion", {
            "fields": (
                "billing_address",
                "billing_postal_code",
                "billing_city",
                "billing_province",
                "billing_country",
            ),
        }),
        ("Contacto y factura", {
            "fields": (
                "billing_phone",
                "billing_email",
                "billing_bank_account",
                "billing_logo",
                "billing_ler_code",
                "billing_footer",
            ),
        }),
        ("Control", {
            "fields": ("data_hash", "created_date"),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SaleLine)
class SaleLineAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sale",
        "position",
        "product_description",
        "quantity",
        "unit",
        "unit_price",
        "tax_rate",
        "subtotal",
        "tax_amount",
        "total",
    )
    search_fields = (
        "sale__invoice_number",
        "sale__buyer__fiscal_name",
        "sale__buyer__tax_id",
        "product_description",
    )
    list_filter = ("sale__company", "unit", "tax_rate")
    autocomplete_fields = ("sale",)
    list_select_related = ("sale", "sale__company", "sale__buyer")
    ordering = ("-sale__invoice_date", "sale_id", "position")
    readonly_fields = ("subtotal", "tax_amount", "total")
    fieldsets = (
        ("Factura", {
            "fields": ("sale", "position"),
        }),
        ("Concepto", {
            "fields": (
                "product_description",
                "quantity",
                "unit",
                "unit_price",
                "tax_rate",
            ),
        }),
        ("Totales calculados", {
            "fields": ("subtotal", "tax_amount", "total"),
        }),
    )

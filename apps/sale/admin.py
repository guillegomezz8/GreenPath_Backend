from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from apps.sale.models import Buyer, Sale


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
    list_display = ("id", "invoice_number", "invoice_date", "buyer", "company", "total", "currency")
    search_fields = ("invoice_number", "buyer__fiscal_name", "buyer__tax_id", "product_description", "notes")
    list_filter = ("company", "invoice_date", "currency", "tax_rate")
    autocomplete_fields = ("company", "buyer")
    list_select_related = ("company", "buyer")
    ordering = ("-invoice_date", "-id")
    date_hierarchy = "invoice_date"
    readonly_fields = ("subtotal", "tax_amount", "total")
    fieldsets = (
        ("Factura", {
            "fields": ("company", "buyer", "manual_invoice_number", "invoice_date", "currency"),
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

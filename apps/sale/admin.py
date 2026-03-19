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
    list_display = ("id", "fiscal_name", "tax_id", "company", "city", "phone", "email")
    search_fields = ("fiscal_name", "tax_id", "city", "province", "email", "phone")
    autocomplete_fields = ("company",)
    ordering = ("fiscal_name",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    form = SaleAdminForm
    list_display = ("id", "invoice_number", "invoice_date", "buyer", "company", "total", "currency")
    search_fields = ("invoice_number", "buyer__fiscal_name", "buyer__tax_id", "product_description")
    autocomplete_fields = ("company", "buyer")
    ordering = ("-invoice_date", "-id")
    readonly_fields = ("subtotal", "tax_amount", "total", "invoice_generated_at")
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
        ("PDF y trazabilidad", {
            "fields": ("invoice_pdf", "invoice_generated_at", "disabled"),
        }),
        ("Notas", {
            "fields": ("notes",),
        }),
    )

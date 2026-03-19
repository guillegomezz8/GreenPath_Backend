from django.contrib import admin

from apps.sale.models import Buyer, Sale


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ("id", "fiscal_name", "tax_id", "company", "city", "phone", "email")
    search_fields = ("fiscal_name", "tax_id", "city", "province", "email", "phone")
    autocomplete_fields = ("company",)
    ordering = ("fiscal_name",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice_number", "invoice_date", "buyer", "company", "total", "currency")
    search_fields = ("invoice_number", "buyer__fiscal_name", "buyer__tax_id", "product_description")
    autocomplete_fields = ("company", "buyer")
    ordering = ("-invoice_date", "-id")

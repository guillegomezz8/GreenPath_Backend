from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.gis.admin import GISModelAdmin

from apps.company.models import Company, CompanyHub, CompanySettings


class CompanyHubInline(admin.StackedInline):
    model = CompanyHub
    extra = 0
    max_num = 1
    can_delete = False
    fields = ("name", "location")


class CompanySettingsInline(admin.StackedInline):
    model = CompanySettings
    extra = 0
    max_num = 1
    can_delete = False
    fields = (
        "default_price_per_liter",
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
        "billing_ler_code",
        "billing_footer",
    )


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "email", "phone", "has_hub", "hub_link")
    search_fields = ("name", "cif", "email", "phone", "owner__email", "owner__username")
    list_filter = ()
    autocomplete_fields = ("owner",)
    inlines = (CompanyHubInline, CompanySettingsInline)
    ordering = ("name",)

    @admin.display(description="Hub")
    def has_hub(self, obj):
        return hasattr(obj, "hub") and obj.hub is not None

    @admin.display(description="Editar hub")
    def hub_link(self, obj):
        if not hasattr(obj, "hub") or not obj.hub:
            return "-"
        url = reverse("admin:company_companyhub_change", args=[obj.hub.id])
        return format_html('<a href="{}">Abrir</a>', url)


@admin.register(CompanyHub)
class CompanyHubAdmin(GISModelAdmin):
    list_display = ("id", "company", "name", "has_location", "edit_company_link")
    search_fields = ("name", "company__name")
    autocomplete_fields = ("company",)
    ordering = ("company__name",)

    @admin.display(description="Ubicación")
    def has_location(self, obj):
        return bool(obj.location)

    @admin.display(description="Empresa")
    def edit_company_link(self, obj):
        url = reverse("admin:company_company_change", args=[obj.company.id])
        return format_html('<a href="{}">Editar empresa</a>', url)


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "default_price_per_liter", "billing_business_name", "billing_tax_id")
    search_fields = ("company__name",)
    autocomplete_fields = ("company",)
    ordering = ("company__name",)

from django.contrib import admin

from apps.bulk_collection.models import BulkCollection
from apps.company.models import CompanySettings


@admin.register(BulkCollection)
class BulkCollectionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "collection_date", "client", "company", "unit", "quantity",
        "unit_price", "total_price", "billable", "invoice_file", "calculation_mode",
    )
    list_filter = ("company", "unit", "billable", "calculation_mode", "collection_date")
    search_fields = ("client__name", "client__cif", "notes")
    autocomplete_fields = ("company", "client")
    date_hierarchy = "collection_date"
    ordering = ("-collection_date", "-id")

    def has_module_permission(self, request):
        module_enabled = CompanySettings.objects.filter(
            bulk_collections_enabled=True,
        ).exists()
        return module_enabled and super().has_module_permission(request)

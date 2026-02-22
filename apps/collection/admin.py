from django.contrib import admin

from apps.collection.models import Collection, CollectionRequest
from apps.base.enums import CollectionStatus


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "collection_date",
        "collection_type",
        "planned_route_day",
        "worker",
        "status",
        "estimated_liters",
        "net_liters",
        "total_price_display",
    )

    list_filter = (
        "status",
        "collection_date",
        "container_type",
        "worker",
    )

    search_fields = (
        "client__name",
        "worker__name",
        "notes",
        "route_day_client__route_day__route__name",
    )

    date_hierarchy = "collection_date"
    ordering = ("-collection_date", "-id")

    readonly_fields = (
        "estimated_liters",
        "net_liters",
        "total_price",
    )

    autocomplete_fields = (
        "client",
        "worker",
        "route_day_client",
    )

    fieldsets = (
        ("Información General", {
            "fields": (
                "client",
                "worker",
                "collection_date",
                "status",
                "route_day_client",
            )
        }),
        ("Contenedores (registro en campo)", {
            "fields": (
                "container_type",
                "container_number",
                "estimated_liters",
            )
        }),
        ("Medición y descuentos (revisión)", {
            "fields": (
                "measured_liters",
                "deduction_liters",
                "deduction_reason",
                "deduction_notes",
            )
        }),
        ("Facturación", {
            "fields": (
                "price_per_liter",
                "net_liters",
                "total_price",
            )
        }),
        ("Notas", {
            "fields": ("notes",)
        }),
    )

    actions = [
        "mark_as_confirmed",
        "mark_as_canceled",
    ]

    @admin.display(description="Tipo")
    def collection_type(self, obj: Collection):
        return "Manual" if obj.route_day_client_id is None else "De ruta"

    @admin.display(description="Ruta diaria")
    def planned_route_day(self, obj: Collection):
        if not obj.route_day_client_id:
            return "-"
        rd = obj.route_day_client.route_day
        return f"{rd.route.name} - {rd.date.strftime('%d/%m/%Y')}"

    @admin.display(description="Precio Total (€)", ordering="total_price")
    def total_price_display(self, obj: Collection):
        if obj.total_price is None:
            return "-"
        return f"{obj.total_price:.2f} €"

    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status=CollectionStatus.CONFIRMED)
        self.message_user(request, f"{updated} recogida(s) marcadas como confirmadas.")

    mark_as_confirmed.short_description = "Marcar como confirmadas"

    def mark_as_canceled(self, request, queryset):
        updated = queryset.update(status=CollectionStatus.CANCELED)
        self.message_user(request, f"{updated} recogida(s) marcadas como canceladas.")

    mark_as_canceled.short_description = "Marcar como canceladas"



@admin.register(CollectionRequest)
class CollectionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "route_day",
        "client",
        "status",
        "expires_at",
        "container_type",
        "container_number",
        "final_liters",
        "final_source",
    )

    list_filter = (
        "status",
        "final_source",
        "container_type",
        "expires_at",
        "route_day_client__route_day__date",
        "route_day_client__route_day__route",
    )

    search_fields = (
        "route_day_client__client__name",
        "route_day_client__route_day__route__name",
    )

    ordering = ("-id",)

    autocomplete_fields = ("route_day_client",)

    readonly_fields = (
        "estimated_liters",
        "final_liters",
        "final_source",
    )

    fieldsets = (
        ("Información", {
            "fields": (
                "route_day_client",
                "status",
                "expires_at",
            )
        }),
        ("Respuesta del cliente", {
            "fields": (
                "container_type",
                "container_number",
            )
        }),
        ("Cálculo / Resultado", {
            "fields": (
                "estimated_liters",
                "final_liters",
                "final_source",
            )
        }),
    )

    @admin.display(description="Ruta diaria")
    def route_day(self, obj):
        if not obj.route_day_client_id:
            return "-"
        rd = obj.route_day_client.route_day
        return f"{rd.route.name} - {rd.date.strftime('%d/%m/%Y')}"

    @admin.display(description="Cliente")
    def client(self, obj):
        if not obj.route_day_client_id:
            return "-"
        return obj.route_day_client.client.name
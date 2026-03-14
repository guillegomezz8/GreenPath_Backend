from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum

from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay
from apps.collection.models import Collection


class RouteDayClientInline(admin.TabularInline):
    model = RouteDayClient
    extra = 0
    fields = ("order", "client")
    ordering = ("order",)
    autocomplete_fields = ("client",)


class RouteDayInline(admin.TabularInline):
    model = RouteDay
    extra = 0
    fields = ("date", "status", "started_at", "finished_at", "admin_link")
    readonly_fields = ("admin_link",)
    ordering = ("-date",)


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0
    fields = (
        "collection_date",
        "client",
        "worker",
        "container_type",
        "container_number",
        "net_liters",
        "total_price",
        "status",
    )
    readonly_fields = ("net_liters", "total_price")
    autocomplete_fields = ("client", "worker")
    ordering = ("-collection_date",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "worker", "start_date", "end_date")
    list_filter = ("company", "week_start", "week_end")
    search_fields = ("name", "company__name")
    ordering = ("-start_date",)
    autocomplete_fields = ("company", "worker")
    date_hierarchy = "start_date"
    inlines = (RouteDayInline,)


@admin.register(RouteDay)
class RouteDayAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "route",
        "date",
        "status",
        "started_at",
        "finished_at",
        "duration",
        "clients_count",
        "admin_link",
    )
    list_filter = ("status", "route", "date")
    search_fields = ("route__name",)
    ordering = ("-date",)
    date_hierarchy = "date"
    autocomplete_fields = ("route",)
    inlines = (RouteDayClientInline,)

    def admin_link(self, obj):
        url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change",
            args=[obj.pk],
        )
        return format_html('<a href="{}">Abrir</a>', url)
    admin_link.short_description = "Link"

    def clients_count(self, obj):
        return obj.ordered_clients.count()
    clients_count.short_description = "Clientes"

    def duration(self, obj):
        if not obj.started_at or not obj.finished_at:
            return "-"
        delta = obj.finished_at - obj.started_at
        total_minutes = int(delta.total_seconds() // 60)
        h, m = divmod(total_minutes, 60)
        return f"{h}h {m}m"
    duration.short_description = "Duración"


@admin.register(RouteDayClient)
class RouteDayClientAdmin(admin.ModelAdmin):
    list_display = ("id", "route_day", "client", "order")
    list_filter = ("route_day__route", "route_day__date")
    search_fields = ("client__name", "route_day__route__name")
    ordering = ("route_day__date", "order")
    autocomplete_fields = ("route_day", "client")


@admin.register(RouteZoneDay)
class RouteZoneDayAdmin(admin.ModelAdmin):
    list_display = ("id", "route", "weekday", "zones_count")
    list_filter = ("route", "weekday")
    search_fields = ("route__name",)
    autocomplete_fields = ("route", "zones")
    filter_horizontal = ("zones",)

    def zones_count(self, obj):
        return obj.zones.count()
    zones_count.short_description = "Zonas"

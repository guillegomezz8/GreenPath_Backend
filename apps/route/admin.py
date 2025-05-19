from django.contrib import admin
from apps.route.models import Route, RouteDay, RouteDayClient
from apps.collection.models import Collection


class CollectionInline(admin.TabularInline):
    model = Collection
    extra = 0
    fields = (
        'client', 'worker', 'collection_date',
        'container_type', 'container_number',
        'liters_collected', 'total_price', 'status'
    )
    readonly_fields = ('liters_collected', 'total_price')


class RouteDayInline(admin.TabularInline):
    model = RouteDay
    extra = 0
    fields = ('date', 'name', 'date_generated')
    readonly_fields = ('date_generated',)
    ordering = ('date',)


class RouteDayClientInline(admin.TabularInline):
    model = RouteDayClient
    extra = 0
    fields = ('client', 'order')
    ordering = ('order',)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company', 'frequency', 'start_date', 'end_date')
    list_filter = ('company', 'frequency', 'week_start')
    search_fields = ('name',)
    ordering = ('-start_date',)
    inlines = [CollectionInline, RouteDayInline]


@admin.register(RouteDay)
class RouteDayAdmin(admin.ModelAdmin):
    list_display = ('route', 'date', 'name')
    list_filter = ('route', 'date')
    ordering = ('-date',)
    inlines = [RouteDayClientInline]

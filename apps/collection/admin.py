from django.contrib import admin
from django.utils.html import format_html
from apps.collection.models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'collection_date',
        'route',
        'worker',
        'status',
        'liters_collected',
        'total_price_display'
    )
    list_filter = ('status', 'collection_date', 'container_type', 'route', 'worker')
    search_fields = ('client__name', 'route__name', 'worker__name')
    date_hierarchy = 'collection_date'
    ordering = ('-collection_date',)
    readonly_fields = ('liters_collected', 'total_price')
    autocomplete_fields = ('client', 'route', 'worker')
    
    fieldsets = (
        ('Información General', {
            'fields': ('client', 'route', 'worker', 'collection_date', 'status')
        }),
        ('Detalles del Contenedor', {
            'fields': ('container_type', 'container_number')
        }),
        ('Cálculos', {
            'fields': ('liters_collected', 'price_per_liter', 'total_price'),
        }),
    )

    actions = ['mark_as_completed']

    @admin.display(description="Precio Total (€)", ordering='total_price')
    def total_price_display(self, obj):
        return f"{obj.total_price:.2f} €" if obj.total_price is not None else "-"

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} recogida(s) marcadas como completadas.")
    mark_as_completed.short_description = "Marcar como completadas"


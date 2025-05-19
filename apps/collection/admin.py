from django.contrib import admin
from apps.collection.models import Collection


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'collection_date', 'route', 'worker', 'status', 'liters_collected', 'total_price')
    list_filter = ('status', 'collection_date', 'container_type', 'route', 'worker')
    search_fields = ('client__name', 'route__name')
    date_hierarchy = 'collection_date'
    ordering = ('-collection_date',)

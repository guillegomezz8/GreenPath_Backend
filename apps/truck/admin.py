from django.contrib import admin
from .models import Truck

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ("registration_number", "brand", "model", "year", "fuel", "company", "driver")
    search_fields = ("registration_number", "brand", "model", "driver__user__username", "company__name")
    list_filter = ("company", "status", "fuel", "year")
    ordering = ("registration_number",)
    autocomplete_fields = ("company", "driver")
    readonly_fields = ("id",)

    fieldsets = (
        ("Identificación", {
            "fields": ("id", "registration_number", "brand", "model", "year"),
        }),
        ("Características técnicas", {
            "fields": ("capacity", "fuel"),
        }),
        ("Estado operativo", {
            "fields": ("status",),
            "description": "Situación actual del vehículo en la flota."
        }),
        ("Relaciones", {
            "fields": ("company", "driver"),
        }),
    )

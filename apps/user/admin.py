from django.contrib import admin
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html

from apps.user.models.client import Client
from apps.user.models.user import User
from apps.user.models.worker import Worker


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "role_type_display", "is_active", "is_staff", "last_login")
    search_fields = ("username", "email")
    list_filter = ("is_active", "is_staff", "is_superuser")
    readonly_fields = ("id", "last_login")
    ordering = ("id",)

    fieldsets = (
        ("Cuenta", {
            "fields": ("id", "username", "email", "password"),
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Acceso", {
            "fields": ("last_login",),
        }),
    )

    @admin.display(description="Rol")
    def role_type_display(self, obj):
        return obj.role_type


@admin.register(Client)
class ClientAdmin(GISModelAdmin):
    gis_widget = gis_forms.OSMWidget
    gis_widget_kwargs = {
        "attrs": {
            "map_width": 800,
            "map_height": 500,
            "default_lat": 37.3886,
            "default_lon": -5.9823,
            "default_zoom": 12,
        }
    }
    list_display = (
        "id",
        "name",
        "cif",
        "city",
        "frequency",
        "user_email",
        "companies_display",
        "has_location",
        "disabled",
    )
    search_fields = ("name", "cif", "phone", "address", "city", "user__email", "user__username")
    list_filter = ("disabled", "frequency", "city", "country", "companies")
    autocomplete_fields = ("user",)
    filter_horizontal = ("companies",)
    readonly_fields = ("id", "location_summary")
    list_select_related = ("user",)
    ordering = ("name", "id")
    actions = ("mark_disabled", "mark_enabled")

    fieldsets = (
        ("Cuenta asociada", {
            "fields": ("id", "user", "disabled"),
        }),
        ("Datos del cliente", {
            "fields": ("name", "phone", "cif", "frequency"),
        }),
        ("Direccion y geolocalizacion", {
            "fields": ("address", "city", "postal_code", "country", "location", "location_summary"),
        }),
        ("Empresas", {
            "fields": ("companies",),
        }),
    )

    @admin.display(description="Email")
    def user_email(self, obj):
        if obj.user_id:
            return obj.user.email
        return "-"

    @admin.display(description="Empresas")
    def companies_display(self, obj):
        companies = list(obj.companies.values_list("name", flat=True)[:3])
        if not companies:
            return "-"
        text = ", ".join(companies)
        if obj.companies.count() > 3:
            return f"{text}..."
        return text

    @admin.display(description="Ubicacion", boolean=True)
    def has_location(self, obj):
        return bool(obj.location)

    @admin.display(description="Coordenadas")
    def location_summary(self, obj):
        if not obj.location:
            return "Sin coordenadas"
        return f"{obj.location.y:.6f}, {obj.location.x:.6f}"

    @admin.action(description="Deshabilitar clientes seleccionados")
    def mark_disabled(self, request, queryset):
        queryset.update(disabled=True)

    @admin.action(description="Habilitar clientes seleccionados")
    def mark_enabled(self, request, queryset):
        queryset.update(disabled=False)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "company",
        "role",
        "user_email",
        "phone",
        "assigned_truck",
        "disabled",
    )
    search_fields = ("name", "surname", "dni", "phone", "user__email", "user__username", "company__name")
    list_filter = ("company", "role", "disabled")
    autocomplete_fields = ("user", "company")
    list_select_related = ("user", "company")
    readonly_fields = ("id", "photo_preview")
    ordering = ("company__name", "name", "surname", "id")
    actions = ("mark_disabled", "mark_enabled")

    fieldsets = (
        ("Cuenta asociada", {
            "fields": ("id", "user", "company", "role", "disabled"),
        }),
        ("Datos personales", {
            "fields": ("name", "surname", "dni", "phone", "birth_date", "address"),
        }),
        ("Imagen", {
            "fields": ("photo", "photo_preview"),
        }),
    )

    @admin.display(description="Trabajador")
    def full_name(self, obj):
        return f"{obj.name} {obj.surname}".strip() or f"Worker #{obj.id}"

    @admin.display(description="Email")
    def user_email(self, obj):
        if obj.user_id:
            return obj.user.email
        return "-"

    @admin.display(description="Camion")
    def assigned_truck(self, obj):
        if hasattr(obj, "truck") and obj.truck:
            return obj.truck.registration_number
        return "-"

    @admin.display(description="Foto")
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="120" height="120" style="object-fit: cover; border-radius: 12px;" />',
                obj.photo.url,
            )
        return "No hay foto"

    @admin.action(description="Deshabilitar trabajadores seleccionados")
    def mark_disabled(self, request, queryset):
        queryset.update(disabled=True)

    @admin.action(description="Habilitar trabajadores seleccionados")
    def mark_enabled(self, request, queryset):
        queryset.update(disabled=False)

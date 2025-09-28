from django.contrib import admin
from django.utils.html import format_html
from apps.user.models.user import User
from apps.user.models.client import Client
from apps.user.models.worker import Worker


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'is_active', 'is_staff')
    search_fields = ('email', 'username')
    list_filter = ('is_active', 'is_staff')
    readonly_fields = ('id',)

    fieldsets = (
        ('Información de Usuario', {
            'fields': ('id', 'username', 'email', 'password')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas', {
            'fields': ('last_login',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'city', 'cif', 'disabled')
    search_fields = ('name', 'cif', 'phone')
    list_filter = ('city', 'disabled')
    list_select_related = ('user',)
    readonly_fields = ('id',)

    fieldsets = (
        ('Información de Cliente', {
            'fields': ('id', 'user', 'name', 'phone', 'cif', 'disabled')
        }),
        ('Ubicación', {
            'fields': ('address', 'city', 'postal_code', 'country', 'location')
        }),
        ('Frecuencia de Recogida', {
            'fields': ('frequency',)
        }),
        ('Empresas Asociadas', {
            'fields': ('companies',)
        }),
    )


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'surname', 'company', 'role')
    search_fields = ('name', 'surname', 'dni')
    list_filter = ('company', 'role')

    list_select_related = ('user', 'company')
    readonly_fields = ('id', 'photo_preview')

    fieldsets = (
        ('Información Personal', {
            'fields': ('id', 'user', 'name', 'surname', 'dni', 'phone', 'photo', 'photo_preview', 'disabled')
        }),
        ('Ubicación', {
            'fields': ('address',)
        }),
        ('Datos Laborales', {
            'fields': ('company', 'role')
        }),
    )

    @admin.display(description="Previsualización de Foto")
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" height="150" style="object-fit: cover;"/>', obj.photo.url)
        return "No hay foto"
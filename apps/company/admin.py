from django.contrib import admin
from django.utils.html import format_html
from apps.company.models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'cif', 'owner', 'email')
    search_fields = ('name', 'cif', 'owner__username', 'owner__email')
    list_filter = ('owner',)
    readonly_fields = ('id', 'logo_preview')

    fieldsets = (
        ('Información General', {
            'fields': ('id', 'name', 'cif', 'owner')
        }),
        ('Detalles de Contacto', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Logo', {
            'fields': ('logo', 'logo_preview'),
        }),
    )

    @admin.display(description="Previsualización del Logo")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="200" height="200" style="object-fit: contain;"/>', obj.logo.url)
        return "No hay logo"

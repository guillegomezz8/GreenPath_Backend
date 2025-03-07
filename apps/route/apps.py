from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.route'
    verbose_name = _('Rutas')

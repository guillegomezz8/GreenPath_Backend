from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ZonesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.zone'
    verbose_name = _('Zonas')

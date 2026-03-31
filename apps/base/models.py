from django.db import models
from apps.user.models.user import User

from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    """Modelo base comun para las entidades persistentes del proyecto."""

    id = models.AutoField(primary_key=True)
    disabled = models.BooleanField('Deshabilitado', default=False)
    created_date = models.DateTimeField('Fecha de Creacion', auto_now=False, auto_now_add=True, blank=True, null=True)
    modified_date = models.DateTimeField('Fecha de Modificacion', auto_now=True, auto_now_add=False, blank=True, null=True)
    deleted_date = models.DateTimeField('Fecha de Eliminacion', auto_now=True, auto_now_add=False, blank=True, null=True)
    historical = HistoricalRecords(user_model=User, inherit=True)

    @property
    def _history_user(self):
        return self.changed_by

    @_history_user.setter
    def _history_user(self, value):
        self.changed_by = value

    class Meta:
        abstract = True
        verbose_name = 'Modelo Base'
        verbose_name_plural = 'Modelos Base'

from django.db import models
from apps.user.models.user import User

from simple_history.models import HistoricalRecords

# Create your models here.
class BaseModel(models.Model):
    """Model definition for BaseModel."""

    # TODO: Define fields here
    id = models.AutoField(primary_key=True)
    disabled = models.BooleanField('Deshabilitado', default=False)
    created_date = models.DateTimeField('Fecha de Creación', auto_now=False, auto_now_add=True, blank=True, null=True)
    modified_date = models.DateTimeField('Fecha de Modificación', auto_now=True, auto_now_add=False, blank=True, null=True)
    deleted_date = models.DateTimeField('Fecha de Eliminación', auto_now=True, auto_now_add=False, blank=True, null=True)
    historical = HistoricalRecords(user_model=User, inherit=True)

    @property
    def _history_user(self):
        return self.changed_by

    @_history_user.setter
    def _history_user(self, value):
        self.changed_by = value

    class Meta:
        """Meta definition for BaseModel."""
        abstract = True
        verbose_name = 'Modelo Base'
        verbose_name_plural = 'Modelos Base'

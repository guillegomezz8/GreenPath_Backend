from django.contrib.gis.db import models as geomodels
from django.db import models

from apps.base.models import BaseModel


class Zone(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la zona")
    polygon = geomodels.PolygonField(verbose_name="Polígono geográfico")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"

    def __str__(self):
        return self.name

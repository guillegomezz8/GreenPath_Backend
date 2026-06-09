from django.contrib.gis.db import models as geomodels
from django.db import models

from apps.base.models import BaseModel
from apps.company.models import Company


class Zone(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="zones",
        verbose_name="Empresa",
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de la zona")
    polygon = geomodels.PolygonField(verbose_name="Polígono geográfico")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="uniq_zone_name_per_company",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

from django.db import models
from apps.company.models import Company
from apps.user.models.worker import Worker
from apps.base.models import BaseModel

class Route(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='routes',
        verbose_name='Compañia'
    )
    workers = models.ManyToManyField(
        Worker,
        related_name='routes',
        verbose_name='Trabajadores'
    )
    date = models.DateField('Fecha')
    start_time = models.TimeField('Hora Inicial')
    end_time = models.TimeField('Hora Final',null=True, blank=True)
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('IN_PROGRESS', 'En progreso'),
            ('COMPLETED', 'Completada'),
            ('CANCELED', 'Cancelada')
        ],
        default='PENDING'
    )

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'

    def __str__(self):
        return f'Ruta {self.id} - {self.date}'

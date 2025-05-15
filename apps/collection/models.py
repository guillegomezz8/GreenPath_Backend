from django.db import models
from django.core.validators import MinValueValidator
from apps.user.models.client import Client
from apps.user.models.worker import Worker
from apps.route.models import Route
from apps.base.models import BaseModel

class CollectionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente'
    COMPLETED = 'COMPLETED', 'Completada'
    CANCELED = 'CANCELED', 'Cancelada'

class ContainerType(models.TextChoices):
    BIDONES = 'BIDONES', 'Bidones (60L)'
    IBC = 'IBC', 'IBC (1000L)'

class Collection(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='Cliente'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections',
        verbose_name='Trabajador'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='Ruta'
    )
    collection_date = models.DateTimeField('Fecha de Recogida')
    container_type = models.CharField(
        'Tipo de Envase',
        max_length=10,
        choices=ContainerType.choices,
        default=ContainerType.BIDONES
    )
    liters_collected = models.DecimalField(
        'Litros Recolectados',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_per_liter = models.DecimalField(
        'Precio por Litro',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        'Precio Total',
        max_digits=10,
        decimal_places=2,
        editable=False
    )
    status = models.CharField(
        'Estado',
        max_length=20,
        choices=CollectionStatus.choices,
        default=CollectionStatus.PENDING
    )

    class Meta:
        verbose_name = 'Recogida'
        verbose_name_plural = 'Recogidas'

    def save(self, *args, **kwargs):
        self.total_price = self.liters_collected * self.price_per_liter
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Recogida {self.id} - {self.client.name} - {self.collection_date}'

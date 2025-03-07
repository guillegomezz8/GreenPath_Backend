from django.db import models
from apps.client.models import Client
from apps.user.models.worker import Worker
from apps.route.models import Route
from apps.base.models import BaseModel

class Collection(BaseModel):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='collections'
    )
    worker = models.ForeignKey(
        Worker,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collections'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='collections'
    )
    collection_date = models.DateTimeField()
    liters_collected = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    price_per_liter = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pendiente'),
            ('COMPLETED', 'Completada'),
            ('CANCELED', 'Cancelada')
        ],
        default='PENDING'
    )

    class Meta:
        verbose_name = 'Recogida'
        verbose_name_plural = 'Recogidas'

    def __str__(self):
        return f'Recogida {self.id} - {self.client.name} - {self.collection_date}'

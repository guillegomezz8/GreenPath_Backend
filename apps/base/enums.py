from django.db import models


class Role(models.TextChoices):
    OWNER = 'owner', 'Dueño'
    WORKER = 'worker', 'Trabajador'


class PickupFrequency(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Semanal'
    BIWEEKLY = 'BIWEEKLY', 'Quincenal'
    MONTHLY = 'MONTHLY', 'Mensual'


class Weekday(models.IntegerChoices):
    MONDAY = 0, 'Lunes'
    TUESDAY = 1, 'Martes'
    WEDNESDAY = 2, 'Miércoles'
    THURSDAY = 3, 'Jueves'
    FRIDAY = 4, 'Viernes'
    SATURDAY = 5, 'Sábado'
    SUNDAY = 6, 'Domingo'


class CollectionStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente'
    COMPLETED = 'COMPLETED', 'Completada'
    CANCELED = 'CANCELED', 'Cancelada'


class ContainerType(models.TextChoices):
    BIDONES = 'BIDONES', 'Bidones (60L)'
    IBC = 'IBC', 'IBC (1000L)'
    
class RouteFrequency(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Semanal'
    MONTHLY = 'MONTHLY', 'Mensual'
    TEMPORAL = 'TEMPORAL', 'Temporal'

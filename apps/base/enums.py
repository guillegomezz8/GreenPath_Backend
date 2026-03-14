from django.db import models


class Role(models.TextChoices):
    OWNER = 'owner', 'Dueño'
    WORKER = 'worker', 'Trabajador'


class PickupFrequency(models.TextChoices):
    WEEKLY = "WEEKLY", "Cada semana"
    TWO_WEEKS = "2_WEEKS", "Cada 2 semanas"
    THREE_WEEKS = "3_WEEKS", "Cada 3 semanas"
    FOUR_WEEKS = "4_WEEKS", "Cada 4 semanas"


class Weekday(models.IntegerChoices):
    MONDAY = 0, 'Lunes'
    TUESDAY = 1, 'Martes'
    WEDNESDAY = 2, 'Miércoles'
    THURSDAY = 3, 'Jueves'
    FRIDAY = 4, 'Viernes'
    SATURDAY = 5, 'Sábado'
    SUNDAY = 6, 'Domingo'


class ContainerType(models.TextChoices):
    BIDONES = 'BIDONES', 'Bidones (60L)'
    IBC = 'IBC', 'IBC (1000L)'


class RouteFrequency(models.TextChoices):
    WEEKLY = 'WEEKLY', 'Semanal'
    MONTHLY = 'MONTHLY', 'Mensual'
    TEMPORAL = 'TEMPORAL', 'Temporal'


class TruckStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Activo"
    IN_SERVICE = "IN_SERVICE", "En servicio"
    MAINTENANCE = "MAINTENANCE", "Mantenimiento"
    OUT_OF_SERVICE = "OUT_OF_SERVICE", "Fuera de servicio"
    DECOMMISSIONED = "DECOMMISSIONED", "Retirado"


class Fuel(models.TextChoices):
    DIESEL = "DIESEL", "Diésel"
    PETROL = "PETROL", "Gasolina"
    ELECTRIC = "ELECTRIC", "Eléctrico"
    HYBRID = "HYBRID", "Híbrido"


class RouteDayStatus(models.TextChoices):
    PLANNED = "PLANNED", "Planificada"
    IN_PROGRESS = "IN_PROGRESS", "En progreso"
    COMPLETED = "COMPLETED", "Completada"
    PARTIAL = "PARTIAL", "Parcial"
    CANCELED = "CANCELED", "Cancelada"


class CollectionStatus(models.TextChoices):
    PENDING_MEASUREMENT = "PENDING_MEASUREMENT", "Pendiente de medición"
    CONFIRMED = "CONFIRMED", "Confirmada"
    CANCELED = "CANCELED", "Cancelada"


class DeductionReason(models.TextChoices):
    WATER = "WATER", "Agua"
    RESIDUE = "RESIDUE", "Residuos/posos"
    MIXED = "MIXED", "Mezcla/impurezas"
    OTHER = "OTHER", "Otros"


class CollectionRequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    ANSWERED = "ANSWERED", "Respondida"
    AUTO_ESTIMATED = "AUTO_ESTIMATED", "Autoestimada"
    MANUAL = "MANUAL", "Manual"


class PlannedSource(models.TextChoices):
    CLIENT = "CLIENT", "Cliente"
    AUTO = "AUTO", "Automático"
    MANUAL = "MANUAL", "Manual"
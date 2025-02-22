from django.db import models

class Role(models.TextChoices):
    OWNER = 'owner', 'Dueño'
    WORKER = 'worker', 'Trabajador'

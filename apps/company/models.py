from django.db import models
from django.core.exceptions import ValidationError
from apps.base.models import BaseModel
from apps.user.models.user import User
from apps.base.enums import Role

class Company(BaseModel):
    name = models.CharField('Nombre', max_length=255)
    address = models.CharField('Dirección', max_length=255, blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email = models.EmailField('Email', max_length=255, blank=True, null=True)
    cif = models.CharField('CIF', max_length=20, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='logo/', max_length=255, null=True, blank=True)

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='companies',
        verbose_name='Dueño'
    )

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.name

    def clean(self):
        """
        Validación para asegurarse de que el dueño tenga el rol de Owner.
        """
        if self.owner and self.owner.role_type and self.owner.role_type != Role.OWNER:
            raise ValidationError({'owner': 'El dueño debe tener el rol de "owner".'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

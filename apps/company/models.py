from django.db import models
from apps.base.models import BaseModel
from apps.user.models.user import User
 
class Company(BaseModel):
    name = models.CharField('Nombre', max_length=255)
    address = models.CharField('Dirección', max_length=255, blank=True, null=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    email = models.EmailField('Email', max_length=255, blank=True, null=True)
    cif = models.CharField('CIF', max_length=20, blank=True, null=True)
    logo = models.ImageField('Logo', upload_to='logo/', max_length=255, null=True, blank=True)

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='companies')

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.name
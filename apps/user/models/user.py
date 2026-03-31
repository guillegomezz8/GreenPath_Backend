from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from simple_history.models import HistoricalRecords
from apps.base.enums import Role

class UserManager(BaseUserManager):
    def _create_user(self, username, email, password, is_staff, is_superuser, **extra_fields):
        user = self.model(
            username=username,
            email=email,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        return self._create_user(username, email, password, False, False, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        return self._create_user(username, email, password, True, True, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField('Nombre de Usuario', max_length=255, unique=True)
    email = models.EmailField('Email', max_length=255, unique=True)

    is_active = models.BooleanField('Esta Activo', default=True)
    is_staff = models.BooleanField('Es Staff', default=False)

    historical = HistoricalRecords()

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.email} - {self.username}'

    @property
    def role_type(self):
        if hasattr(self, 'worker_profile'):
            return "owner" if self.worker_profile.role == Role.OWNER else "worker"
        if hasattr(self, 'client_profile'):
            return "client"
        return "desconocido"

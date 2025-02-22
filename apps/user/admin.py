from django.contrib import admin

from apps.user.models.user import User
from apps.user.models.client import Client
from apps.user.models.worker import Worker

admin.site.register(User)
admin.site.register(Client)
admin.site.register(Worker)

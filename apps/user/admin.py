from django.contrib import admin
from apps.user.models.user import User
from apps.user.models.client import Client, ClientPickupSchedule
from apps.user.models.worker import Worker


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'is_active', 'is_staff')
    search_fields = ('email',)
    list_filter = ('is_active', 'is_staff')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'city', 'cif')
    search_fields = ('name', 'cif', 'phone')
    list_filter = ('city', 'country')


@admin.register(ClientPickupSchedule)
class ClientPickupScheduleAdmin(admin.ModelAdmin):
    list_display = ('client', 'company', 'weekday', 'frequency')
    list_filter = ('weekday', 'frequency', 'company')
    search_fields = ('client__name',)


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'surname', 'company', 'role')
    list_filter = ('company', 'role')
    search_fields = ('name', 'surname', 'dni')

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from django.db.models import Q

from apps.zone.models import Zone
from apps.zone.api.serializers.zone_serializers import (
    ZoneSerializer,
    CreateZoneSerializer,
    UpdateZoneSerializer,
)
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser
from apps.company.utils import resolve_user_company

configure_logging()

class ZoneFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    search = CharFilter(method='filter_search')

    class Meta:
        model = Zone
        fields = ['name', 'search']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
        )


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.select_related("company").all().order_by('name')
    filter_backends = [DjangoFilterBackend]
    filterset_class = ZoneFilter
    permission_classes = [IsAuthenticated, IsOwnerUser]

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return base_qs.none()
        if user.is_staff or user.is_superuser:
            return base_qs

        company = resolve_user_company(user)
        if company is None:
            return base_qs.none()
        return base_qs.filter(company=company)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateZoneSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateZoneSerializer
        return ZoneSerializer

    def perform_create(self, serializer):
        company = resolve_user_company(self.request.user)
        if company is None:
            raise serializers.ValidationError({"company": "No se pudo resolver la empresa del usuario."})
        serializer.save(company=company)

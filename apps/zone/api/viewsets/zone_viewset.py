from rest_framework import viewsets
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
import logging

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
    queryset = Zone.objects.all().order_by('name')
    filter_backends = [DjangoFilterBackend]
    filterset_class = ZoneFilter
    permission_classes = [IsAuthenticated, IsOwnerUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateZoneSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateZoneSerializer
        return ZoneSerializer

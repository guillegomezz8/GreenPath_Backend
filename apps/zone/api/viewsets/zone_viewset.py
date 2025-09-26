from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter
from apps.zone.models import Zone
from apps.zone.api.serializers.zone_serializers import (
    ZoneSerializer,
    CreateZoneSerializer,
    UpdateZoneSerializer,
)
from apps.base.logger import configure_logging
import logging

configure_logging()

class ZoneFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Zone
        fields = ['name']


class ZoneViewSet(viewsets.ModelViewSet):
    queryset = Zone.objects.all().order_by('name')
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = ZoneFilter
    search_fields = ['name']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateZoneSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateZoneSerializer
        return ZoneSerializer

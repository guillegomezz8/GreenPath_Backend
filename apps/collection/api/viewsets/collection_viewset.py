from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import (
    FilterSet, CharFilter, DjangoFilterBackend
)
from apps.base.logger import configure_logging
from apps.collection.models import Collection
from apps.base.permissions import IsOwnerUser
from apps.collection.api.serializers.collection_serializers import (
    CollectionSerializer,
    CreateCollectionSerializer,
    UpdateCollectionSerializer,
    PartialUpdateCollectionSerializer
)
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_COLLECTION
)
import logging

configure_logging()


class CollectionFilter(FilterSet):
    client = CharFilter(field_name='client__name', lookup_expr='icontains')
    worker = CharFilter(field_name='worker__name', lookup_expr='icontains')
    status = CharFilter(field_name='status', lookup_expr='icontains')

    class Meta:
        model = Collection
        fields = ['client', 'worker', 'status']


class CollectionViewSet(viewsets.ModelViewSet):
    model = Collection
    queryset = Collection.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = CollectionFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCollectionSerializer
        elif self.action == 'update':
            return UpdateCollectionSerializer
        elif self.action == 'partial_update':
            return PartialUpdateCollectionSerializer
        else:
            return CollectionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action == 'list':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(CollectionViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == 'owner' or self.request.user.role_type == 'worker':
                serializer.save()
            else:
                logging.error("Solo los dueños y trabajadores pueden registrar recogidas")
                raise ValueError("Solo los dueños y trabajadores pueden registrar recogidas")
        except Exception as e:
            logging.error(f"Error creando recogida: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_COLLECTION} - {str(e)}")

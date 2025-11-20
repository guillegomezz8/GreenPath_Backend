from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import FilterSet, CharFilter, DjangoFilterBackend

import logging

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
    ERROR_CREATING_COLLECTION,
    ONLY_OWNERS_AND_WORKERS_CAN_REGISTER_COLLECTIONS,
    INTERNAL_ERROR,
    DETAILS
)

configure_logging()


class CollectionFilter(FilterSet):
    client = CharFilter(field_name='client__name', lookup_expr='icontains')
    worker = CharFilter(field_name='worker__name', lookup_expr='icontains')
    status = CharFilter(field_name='status', lookup_expr='icontains')
    worker_id = CharFilter(field_name='worker__id', lookup_expr='exact')

    class Meta:
        model = Collection
        fields = ['client', 'worker', 'status', 'worker_id']


class CollectionViewSet(viewsets.ModelViewSet):
    model = Collection
    queryset = Collection.objects.all().order_by('-collection_date')
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
                logging.error("[collection_viewset - perform_create] Solo los dueños y trabajadores pueden registrar recogidas")
                raise ValueError(ONLY_OWNERS_AND_WORKERS_CAN_REGISTER_COLLECTIONS)
        except Exception as e:
            logging.error(f"[collection_viewset - perform_create] Error creando recogida: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_COLLECTION} - {str(e)}")
        
    def list(self, request):
        try:
            logging.info(f"[collection_viewset - list] Listando recogidas para usuario {request.user.id}")
            base_queryset = self.get_queryset()
            filtered_queryset = self.filter_queryset(base_queryset)

            page = self.paginate_queryset(filtered_queryset)

            if page is not None:
                items = page
                meta = {
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                }
            else:
                items = filtered_queryset
                meta = {}

            serializer = self.get_serializer(items, many=True)

            response = {
                **meta,  
                "results": serializer.data,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"[collection_viewset - list] Error al listar recogidas: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)
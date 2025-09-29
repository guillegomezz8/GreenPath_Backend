from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action

import django_filters
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Avg, Count, OuterRef, Subquery, DateTimeField
from django.db import transaction
from django_filters.rest_framework import FilterSet, CharFilter, DjangoFilterBackend

import logging

from apps.base.logger import configure_logging
from apps.base.utils import gen_password, send_access_email
from apps.user.models.client import Client
from apps.user.models.user import User
from apps.collection.models import Collection
from apps.base.enums import PickupFrequency
from apps.base.permissions import IsOwnerUser
from apps.collection.api.serializers.collection_serializers import CollectionSerializer
from apps.user.api.serializers.client_serializers import ClientSerializer,CreateClientSerializer,UpdateClientSerializer,PartialUpdateClientSerializer
from apps.base.literals import (
    ERROR,
    ERROR_CREATING_CLIENT,
    DETAILS,
    INTERNAL_ERROR
)

configure_logging()


class ClientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    phone = CharFilter(field_name='phone', lookup_expr='icontains')
    cif = CharFilter(field_name='cif', lookup_expr='icontains')
    address = CharFilter(field_name='address', lookup_expr='icontains')
    frequency = CharFilter(field_name='frequency', lookup_expr='exact')
    search = django_filters.CharFilter(method="filter_search")


    class Meta:
        model = Client
        fields = ['name', 'phone', 'cif', 'address', 'frequency', 'search']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(address__icontains=value)
        )


class ClientViewSet(viewsets.ModelViewSet):
    model = Client
    queryset = Client.objects.filter(disabled=False).order_by('id')
    filter_backends = [DjangoFilterBackend]
    filterset_class = ClientFilter

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(companies=self.request.user.worker_profile.company)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateClientSerializer
        elif self.action == 'update':
            return UpdateClientSerializer
        elif self.action == 'partial_update':
            return PartialUpdateClientSerializer
        else:
            return ClientSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsOwnerUser]
        elif self.action in ['list', 'retrieve', 'collection_historial']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super(ClientViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            logging.info(f"[client_viewset - perform_create] Creando nuevo usuario por usuario {self.request.user.id}")

            client_data = dict(serializer.validated_data)
            user_data = client_data.pop("user")
            get_access = client_data.pop("get_access", False)
            companies = client_data.pop("companies", None)

            company = getattr(getattr(self.request.user, "worker_profile", None), "company", None)

            with transaction.atomic():
                user = User.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=None,
                )

                temp_password = None
                if get_access:
                    temp_password = gen_password()
                    user.set_password(temp_password)
                    transaction.on_commit(lambda: send_access_email(user, temp_password, subject="Acceso a GreenPath como Cliente"))
                else:
                    user.set_unusable_password()

                user.save(update_fields=["password"])

                client = Client.objects.create(user=user, **client_data)

                if companies:
                    client.companies.set(companies)

                if company:
                    client.companies.add(company)

                client.save()

            logging.info(f"[client_viewset - perform_create] Cliente creado con éxito: {client.id}")
        except Exception as e:
            logging.error(f"[client_viewset - perform_create] Error creando cliente: {str(e)}")
            raise Exception(f"{ERROR}: {ERROR_CREATING_CLIENT} - {str(e)}")
        
    def perform_destroy(self, instance):
        try:
            logging.info(f"[client_viewset - perform_destroy] Deshabilitando cliente {instance.id} por usuario {self.request.user.id}")
            instance.disabled = True
            instance.save(update_fields=['disabled'])
            logging.info(f"[client_viewset - perform_destroy] Cliente deshabilitado con éxito: {instance.id}")
        except Exception as e:
            logging.error(f"[client_viewset - perform_destroy] Error eliminando cliente: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            logging.info(f"[client_viewset - list] Listando clientes para usuario {request.user.id}")
            base_queryset = self.get_queryset()
            filtered_queryset = self.filter_queryset(base_queryset)

            counts = base_queryset.aggregate(
                every_week=Count('id', filter=Q(frequency=PickupFrequency.WEEKLY)),
                every_2_weeks=Count('id', filter=Q(frequency=PickupFrequency.TWO_WEEKS)),
                every_3_weeks=Count('id', filter=Q(frequency=PickupFrequency.THREE_WEEKS)),
                every_4_weeks=Count('id', filter=Q(frequency=PickupFrequency.FOUR_WEEKS)),
            )

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
                "counts": counts,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"[client_viewset - list] Error al listar clientes: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path=r'historial/(?P<client_id>\d+)')
    def collection_historial(self, request, client_id=None):
        try:
            logging.info(f"[client_viewset - collection_historial] Obteniendo historial de cliente {client_id} para usuario {request.user.id}")
            client = get_object_or_404(Client, id=client_id)

            historial = Collection.objects.filter(client=client, worker__company=request.user.worker_profile.company).order_by('-collection_date')
            aggregates = historial.aggregate(
                total_liters=Sum('liters_collected'),
                avg_liters=Avg('liters_collected')
            )

            serializer = CollectionSerializer(historial, many=True)

            total_liters = aggregates.get('total_liters') or 0
            avg_liters = aggregates.get('avg_liters') or 0

            response_data = {
                "historial": serializer.data,
                "total_liters": total_liters,
                "media": round(avg_liters, 2),
            }

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logging.error(f"[client_viewset - collection_historial] Error al obtener historial: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_400_BAD_REQUEST)
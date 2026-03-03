import logging

from django.utils import timezone
from django.db.models import Q
from django_filters.rest_framework import FilterSet, CharFilter, DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.enums import CollectionRequestStatus, PlannedSource
from apps.base.literals import (
    COLLECTION_REQUEST_ANSWERED_SUCCESS,
    COLLECTION_REQUEST_CLIENT_FORBIDDEN,
    COLLECTION_REQUEST_CLIENT_LIST_FORBIDDEN,
    COLLECTION_REQUEST_COMPANY_FORBIDDEN,
    COLLECTION_REQUEST_EXPIRED,
    COLLECTION_REQUEST_MANUAL_FORBIDDEN,
    COLLECTION_REQUEST_MANUAL_SUCCESS,
    COLLECTION_REQUEST_NOT_FOUND,
    COLLECTION_REQUEST_NOT_PENDING,
    DETAILS,
    ERROR,
    ERROR_CREATING_COLLECTION,
    INTERNAL_ERROR,
    MESSAGE,
    ONLY_OWNERS_AND_WORKERS_CAN_REGISTER_COLLECTIONS,
)
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser
from apps.collection.api.serializers.collection_serializers import (
    AnswerCollectionRequestSerializer,
    CollectionRequestSerializer,
    CollectionSerializer,
    CreateCollectionSerializer,
    ManualCollectionRequestSerializer,
    PartialUpdateCollectionSerializer,
    UpdateCollectionSerializer,
)
from apps.collection.models import Collection, CollectionRequest

configure_logging()


class CollectionFilter(FilterSet):
    client = CharFilter(field_name="client__name", lookup_expr="icontains")
    worker = CharFilter(field_name="worker__name", lookup_expr="icontains")
    status = CharFilter(field_name="status", lookup_expr="icontains")
    worker_id = CharFilter(field_name="worker__id", lookup_expr="exact")
    search = CharFilter(method="filter_search")

    class Meta:
        model = Collection
        fields = ["client", "worker", "status", "worker_id", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(client__name__icontains=value) |
            Q(client__cif__icontains=value) |
            Q(worker__name__icontains=value) |
            Q(worker__surname__icontains=value) |
            Q(notes__icontains=value) |
            Q(status__icontains=value) |
            Q(route_day_client__route_day__route__name__icontains=value)
        ).distinct()


def _user_company_id(user):
    if not hasattr(user, "worker_profile"):
        return None
    return user.worker_profile.company_id


class CollectionViewSet(viewsets.ModelViewSet):
    model = Collection
    queryset = Collection.objects.all().order_by("-collection_date")
    filter_backends = [DjangoFilterBackend]
    filterset_class = CollectionFilter

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return base_qs.none()
        if user.is_staff or user.is_superuser:
            return base_qs
        if user.role_type == "client" and hasattr(user, "client_profile"):
            return base_qs.filter(client_id=user.client_profile.id)
        if user.role_type == "owner" and hasattr(user, "worker_profile"):
            company_id = user.worker_profile.company_id
            return base_qs.filter(
                Q(client__companies__id=company_id) |
                Q(worker__company_id=company_id) |
                Q(route_day_client__route_day__route__company_id=company_id)
            ).distinct()
        if user.role_type == "worker" and hasattr(user, "worker_profile"):
            return base_qs.filter(worker_id=user.worker_profile.id)
        return base_qs.none()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCollectionSerializer
        elif self.action == "update":
            return UpdateCollectionSerializer
        elif self.action == "partial_update":
            return PartialUpdateCollectionSerializer
        elif self.action == "answer_request":
            return AnswerCollectionRequestSerializer
        elif self.action == "manual_request":
            return ManualCollectionRequestSerializer
        return CollectionSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = [IsAuthenticated, IsOwnerUser]
        elif self.action == "list":
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated]
        return super(CollectionViewSet, self).get_permissions()

    def perform_create(self, serializer):
        try:
            if self.request.user.role_type == "owner":
                serializer.save()
            elif self.request.user.role_type == "worker" and hasattr(self.request.user, "worker_profile"):
                serializer.save(worker=self.request.user.worker_profile)
            else:
                logging.error("[collection_viewset - perform_create] Solo los duenos y trabajadores pueden registrar recogidas")
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
                meta = {"count": self.paginator.page.paginator.count, "next": self.paginator.get_next_link(), "previous": self.paginator.get_previous_link()}
            else:
                items = filtered_queryset
                meta = {}

            serializer = self.get_serializer(items, many=True)
            return Response({**meta, "results": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[collection_viewset - list] Error al listar recogidas: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="requests/me")
    def my_requests(self, request):
        try:
            if request.user.role_type != "client" or not hasattr(request.user, "client_profile"):
                logging.warning(f"[collection_viewset - my_requests] Usuario {request.user.id} sin rol cliente para listar solicitudes")
                return Response({DETAILS: COLLECTION_REQUEST_CLIENT_LIST_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            request_status = request.query_params.get("status")
            queryset = CollectionRequest.objects.filter(route_day_client__client=request.user.client_profile).select_related("route_day_client", "route_day_client__client", "route_day_client__route_day", "route_day_client__route_day__route")
            queryset = queryset.filter(status=request_status) if request_status else queryset.filter(status__in=[CollectionRequestStatus.PENDING, CollectionRequestStatus.AUTO_ESTIMATED])
            queryset = queryset.order_by("route_day_client__route_day__date", "expires_at")
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = CollectionRequestSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = CollectionRequestSerializer(queryset, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[collection_viewset - my_requests] Error listando solicitudes del cliente: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path=r"requests/(?P<request_id>\d+)")
    def request_detail(self, request, request_id=None):
        try:
            collection_request = CollectionRequest.objects.filter(id=request_id).select_related("route_day_client", "route_day_client__client", "route_day_client__route_day", "route_day_client__route_day__route").first()
            if not collection_request:
                return Response({DETAILS: COLLECTION_REQUEST_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role_type == "client":
                if not hasattr(request.user, "client_profile") or collection_request.route_day_client.client_id != request.user.client_profile.id:
                    return Response({DETAILS: COLLECTION_REQUEST_CLIENT_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            elif request.user.role_type in ["owner", "worker"]:
                if _user_company_id(request.user) != collection_request.route_day_client.route_day.route.company_id:
                    return Response({DETAILS: COLLECTION_REQUEST_COMPANY_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({DETAILS: COLLECTION_REQUEST_MANUAL_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            return Response(CollectionRequestSerializer(collection_request).data, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[collection_viewset - request_detail] Error recuperando solicitud {request_id}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path=r"requests/(?P<request_id>\d+)/answer")
    def answer_request(self, request, request_id=None):
        try:
            collection_request = CollectionRequest.objects.filter(id=request_id).select_related("route_day_client", "route_day_client__client", "route_day_client__route_day").first()
            if not collection_request:
                return Response({DETAILS: COLLECTION_REQUEST_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role_type != "client" or not hasattr(request.user, "client_profile") or collection_request.route_day_client.client_id != request.user.client_profile.id:
                logging.warning(f"[collection_viewset - answer_request] Usuario {request.user.id} sin permiso para solicitud {request_id}")
                return Response({DETAILS: COLLECTION_REQUEST_CLIENT_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            if collection_request.status not in [CollectionRequestStatus.PENDING, CollectionRequestStatus.AUTO_ESTIMATED]:
                return Response({DETAILS: COLLECTION_REQUEST_NOT_PENDING}, status=status.HTTP_400_BAD_REQUEST)

            if collection_request.is_expired():
                return Response({DETAILS: COLLECTION_REQUEST_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            collection_request.final_liters = serializer.validated_data["final_liters"]
            if collection_request.estimated_liters is None:
                collection_request.estimated_liters = collection_request.final_liters
            collection_request.final_source = PlannedSource.CLIENT
            collection_request.status = CollectionRequestStatus.ANSWERED
            collection_request.answered_by = request.user
            collection_request.answered_at = timezone.now()
            collection_request.save(update_fields=["final_liters", "estimated_liters", "final_source", "status", "answered_by", "answered_at", "modified_date"])
            logging.info(f"[collection_viewset - answer_request] Solicitud {collection_request.id} respondida por cliente {request.user.id}")
            return Response({MESSAGE: COLLECTION_REQUEST_ANSWERED_SUCCESS, "request": CollectionRequestSerializer(collection_request).data}, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[collection_viewset - answer_request] Error respondiendo solicitud {request_id}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"], url_path=r"requests/(?P<request_id>\d+)/manual")
    def manual_request(self, request, request_id=None):
        try:
            collection_request = CollectionRequest.objects.filter(id=request_id).select_related("route_day_client", "route_day_client__client", "route_day_client__route_day", "route_day_client__route_day__route").first()
            if not collection_request:
                return Response({DETAILS: COLLECTION_REQUEST_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            if request.user.role_type not in ["owner", "worker"]:
                logging.warning(f"[collection_viewset - manual_request] Usuario {request.user.id} sin permiso manual para solicitud {request_id}")
                return Response({DETAILS: COLLECTION_REQUEST_MANUAL_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            if _user_company_id(request.user) != collection_request.route_day_client.route_day.route.company_id:
                logging.warning(f"[collection_viewset - manual_request] Usuario {request.user.id} de otra empresa para solicitud {request_id}")
                return Response({DETAILS: COLLECTION_REQUEST_COMPANY_FORBIDDEN}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            collection_request.final_liters = serializer.validated_data["final_liters"]
            if collection_request.estimated_liters is None:
                collection_request.estimated_liters = collection_request.final_liters
            collection_request.final_source = PlannedSource.MANUAL
            collection_request.status = CollectionRequestStatus.MANUAL
            collection_request.manual_by = request.user
            collection_request.manual_at = timezone.now()
            collection_request.save(update_fields=["final_liters", "estimated_liters", "final_source", "status", "manual_by", "manual_at", "modified_date"])
            logging.info(f"[collection_viewset - manual_request] Solicitud {collection_request.id} actualizada manualmente por usuario {request.user.id}")
            return Response({MESSAGE: COLLECTION_REQUEST_MANUAL_SUCCESS, "request": CollectionRequestSerializer(collection_request).data}, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[collection_viewset - manual_request] Error registrando manualmente solicitud {request_id}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

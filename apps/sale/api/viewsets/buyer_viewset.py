import logging

from django.db.models import Q
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.literals import DETAILS, INTERNAL_ERROR
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerUser
from apps.company.utils import resolve_user_company
from apps.sale.api.serializers.buyer_serializers import (
    BuyerSerializer,
    CreateBuyerSerializer,
    PartialUpdateBuyerSerializer,
    UpdateBuyerSerializer,
)
from apps.sale.models import Buyer

configure_logging()


class BuyerFilter(FilterSet):
    fiscal_name = CharFilter(field_name="fiscal_name", lookup_expr="icontains")
    tax_id = CharFilter(field_name="tax_id", lookup_expr="icontains")
    city = CharFilter(field_name="city", lookup_expr="icontains")
    province = CharFilter(field_name="province", lookup_expr="icontains")
    search = CharFilter(method="filter_search")

    class Meta:
        model = Buyer
        fields = ["fiscal_name", "tax_id", "city", "province", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(fiscal_name__icontains=value) |
            Q(tax_id__icontains=value) |
            Q(fiscal_address__icontains=value) |
            Q(city__icontains=value) |
            Q(province__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(contact_person__icontains=value)
        )


class BuyerViewSet(viewsets.ModelViewSet):
    queryset = Buyer.objects.all().order_by("fiscal_name")
    filter_backends = [DjangoFilterBackend]
    filterset_class = BuyerFilter
    permission_classes = [IsAuthenticated, IsOwnerUser]

    def get_queryset(self):
        company = resolve_user_company(self.request.user)
        if not company:
            return super().get_queryset().none()
        return super().get_queryset().filter(company=company)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBuyerSerializer
        if self.action == "update":
            return UpdateBuyerSerializer
        if self.action == "partial_update":
            return PartialUpdateBuyerSerializer
        return BuyerSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["company"] = resolve_user_company(self.request.user)
        return context

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[buyer_viewset - list] Error listando compradores: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            buyer = serializer.save()
            read_serializer = BuyerSerializer(buyer, context=self.get_serializer_context())
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[buyer_viewset - create] Error creando comprador: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            buyer = serializer.save()
            read_serializer = BuyerSerializer(buyer, context=self.get_serializer_context())
            return Response(read_serializer.data, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[buyer_viewset - update] Error actualizando comprador: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

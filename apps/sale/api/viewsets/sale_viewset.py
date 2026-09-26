import io
import logging
from django.db.models import Q
from django.http import FileResponse
from django.utils.dateparse import parse_date
from django_filters.rest_framework import CharFilter, DateFilter, DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.logger import configure_logging
from apps.base.literals import (
    COMPANY_NOT_FOUND,
    DETAILS,
    INTERNAL_ERROR,
    SUMMARY_DATE_ORDER_INVALID,
    SUMMARY_DATE_RANGE_REQUIRED,
    SUMMARY_END_DATE_INVALID,
    SUMMARY_START_DATE_INVALID,
)
from apps.base.permissions import IsOwnerUser
from apps.company.utils import resolve_user_company
from apps.sale.api.serializers.sale_serializers import (
    CreateSaleSerializer,
    PartialUpdateSaleSerializer,
    SaleSerializer,
    UpdateSaleSerializer,
)
from apps.sale.models import Sale
from apps.sale.services.economic_summary import build_economic_summary
from apps.sale.utils import generate_sale_invoice_pdf

configure_logging()


class SaleFilter(FilterSet):
    invoice_number = CharFilter(field_name="invoice_number", lookup_expr="icontains")
    buyer = CharFilter(field_name="buyer__fiscal_name", lookup_expr="icontains")
    invoice_year = CharFilter(field_name="invoice_year", lookup_expr="exact")
    start_date = DateFilter(field_name="invoice_date", lookup_expr="gte")
    end_date = DateFilter(field_name="invoice_date", lookup_expr="lte")
    search = CharFilter(method="filter_search")

    class Meta:
        model = Sale
        fields = ["invoice_number", "buyer", "invoice_year", "start_date", "end_date", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(invoice_number__icontains=value) |
            Q(buyer__fiscal_name__icontains=value) |
            Q(buyer__tax_id__icontains=value) |
            Q(product_description__icontains=value) |
            Q(lines__product_description__icontains=value) |
            Q(unit__icontains=value) |
            Q(notes__icontains=value)
        ).distinct()


def _parse_summary_date_range(query_params):
    start_raw = (query_params.get("start_date") or "").strip()
    end_raw = (query_params.get("end_date") or "").strip()

    if not start_raw and not end_raw:
        return None, None

    if not start_raw or not end_raw:
        raise ValidationError({"date_range": SUMMARY_DATE_RANGE_REQUIRED})

    start_date = parse_date(start_raw)
    if not start_date:
        raise ValidationError({"start_date": SUMMARY_START_DATE_INVALID})

    end_date = parse_date(end_raw)
    if not end_date:
        raise ValidationError({"end_date": SUMMARY_END_DATE_INVALID})

    if start_date > end_date:
        raise ValidationError({"date_range": SUMMARY_DATE_ORDER_INVALID})

    return start_date, end_date


class SaleViewSet(viewsets.ModelViewSet):
    queryset = (
        Sale.objects
        .select_related("company", "buyer", "invoice_issuer")
        .prefetch_related("lines")
        .all()
        .order_by("-invoice_date", "-id")
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = SaleFilter
    permission_classes = [IsAuthenticated, IsOwnerUser]

    def get_queryset(self):
        company = resolve_user_company(self.request.user)
        if not company:
            return super().get_queryset().none()
        return super().get_queryset().filter(company=company)

    def get_serializer_class(self):
        if self.action == "create":
            return CreateSaleSerializer
        if self.action == "update":
            return UpdateSaleSerializer
        if self.action == "partial_update":
            return PartialUpdateSaleSerializer
        return SaleSerializer

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
            logging.error(f"[sale_viewset - list] Error listando ventas: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            sale = serializer.save()
            read_serializer = SaleSerializer(sale, context=self.get_serializer_context())
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[sale_viewset - create] Error creando venta: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            sale = serializer.save()
            read_serializer = SaleSerializer(sale, context=self.get_serializer_context())
            return Response(read_serializer.data, status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[sale_viewset - update] Error actualizando venta: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="invoice/download")
    def download_invoice(self, request, pk=None):
        try:
            sale = self.get_object()
            pdf_content, filename = generate_sale_invoice_pdf(sale)
            return FileResponse(io.BytesIO(pdf_content), as_attachment=True, filename=filename, content_type="application/pdf")
        except Exception as e:
            logging.error(f"[sale_viewset - download_invoice] Error descargando factura de venta {pk}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="economic-summary")
    def economic_summary(self, request):
        try:
            company = resolve_user_company(request.user)
            if not company:
                return Response({DETAILS: COMPANY_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            start_date, end_date = _parse_summary_date_range(request.query_params)
            return Response(build_economic_summary(company, start_date, end_date), status=status.HTTP_200_OK)
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[sale_viewset - economic_summary] Error obteniendo resumen economico: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

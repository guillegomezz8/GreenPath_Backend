import io
import logging

from django.db.models import Q, Sum
from django.http import FileResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django_filters.rest_framework import CharFilter, DateFilter, DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.logger import configure_logging
from apps.base.literals import DETAILS, INTERNAL_ERROR
from apps.base.permissions import IsOwnerUser
from apps.company.utils import resolve_user_company
from apps.sale.api.serializers.sale_serializers import (
    CreateSaleSerializer,
    PartialUpdateSaleSerializer,
    SaleSerializer,
    UpdateSaleSerializer,
)
from apps.sale.models import Sale
from apps.sale.utils import company_collection_cost_queryset, generate_sale_invoice_pdf

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
            Q(unit__icontains=value) |
            Q(notes__icontains=value)
        )


def _monthly_keys(months=6):
    current = timezone.localdate()
    items = []
    for offset in range(months - 1, -1, -1):
        year = current.year
        month = current.month - offset
        while month <= 0:
            month += 12
            year -= 1
        items.append((year, month))
    return items


def _filtered_monthly_keys(start_date=None, end_date=None, months=6):
    if not start_date or not end_date:
        return _monthly_keys(months=months)

    items = []
    current_year = start_date.year
    current_month = start_date.month

    while (current_year, current_month) <= (end_date.year, end_date.month):
        items.append((current_year, current_month))
        if current_month == 12:
            current_year += 1
            current_month = 1
        else:
            current_month += 1
    return items


def _parse_summary_date_range(query_params):
    start_raw = (query_params.get("start_date") or "").strip()
    end_raw = (query_params.get("end_date") or "").strip()

    if not start_raw and not end_raw:
        return None, None

    if not start_raw or not end_raw:
        raise ValidationError({"date_range": "Debes indicar start_date y end_date juntos."})

    start_date = parse_date(start_raw)
    if not start_date:
        raise ValidationError({"start_date": "Formato de fecha invalido. Usa YYYY-MM-DD."})

    end_date = parse_date(end_raw)
    if not end_date:
        raise ValidationError({"end_date": "Formato de fecha invalido. Usa YYYY-MM-DD."})

    if start_date > end_date:
        raise ValidationError({"date_range": "start_date no puede ser posterior a end_date."})

    return start_date, end_date


def _apply_date_range(queryset, field_name, start_date=None, end_date=None):
    if not start_date or not end_date:
        return queryset
    return queryset.filter(**{f"{field_name}__range": (start_date, end_date)})


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("company", "buyer").all().order_by("-invoice_date", "-id")
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
                return Response({DETAILS: "Empresa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            start_date, end_date = _parse_summary_date_range(request.query_params)
            collections_qs = _apply_date_range(
                company_collection_cost_queryset(company),
                "collection_date",
                start_date,
                end_date,
            )
            sales_qs = _apply_date_range(
                Sale.objects.filter(company=company),
                "invoice_date",
                start_date,
                end_date,
            )

            total_cost = collections_qs.aggregate(total=Sum("total_price")).get("total") or 0
            total_income = sales_qs.aggregate(total=Sum("total")).get("total") or 0
            total_bought_volume = collections_qs.aggregate(total=Sum("net_liters")).get("total") or 0
            total_sold_volume = sales_qs.aggregate(total=Sum("quantity")).get("total") or 0

            monthly = []
            for year, month in _filtered_monthly_keys(start_date=start_date, end_date=end_date):
                month_sales = sales_qs.filter(invoice_date__year=year, invoice_date__month=month)
                month_collections = collections_qs.filter(collection_date__year=year, collection_date__month=month)
                income = month_sales.aggregate(total=Sum("total")).get("total") or 0
                cost = month_collections.aggregate(total=Sum("total_price")).get("total") or 0
                sold_volume = month_sales.aggregate(total=Sum("quantity")).get("total") or 0
                bought_volume = month_collections.aggregate(total=Sum("net_liters")).get("total") or 0
                monthly.append({
                    "year": year,
                    "month": month,
                    "income": income,
                    "cost": cost,
                    "profit": income - cost,
                    "sold_volume": sold_volume,
                    "bought_volume": bought_volume,
                })

            return Response(
                {
                    "total_cost": total_cost,
                    "total_income": total_income,
                    "net_profit": total_income - total_cost,
                    "total_bought_volume": total_bought_volume,
                    "total_sold_volume": total_sold_volume,
                    "monthly": monthly,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError:
            raise
        except Exception as e:
            logging.error(f"[sale_viewset - economic_summary] Error obteniendo resumen economico: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

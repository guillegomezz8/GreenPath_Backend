import logging

from django.db.models import Q, Sum
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.logger import configure_logging
from apps.base.literals import DETAILS, INTERNAL_ERROR, MESSAGE
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
    search = CharFilter(method="filter_search")

    class Meta:
        model = Sale
        fields = ["invoice_number", "buyer", "invoice_year", "search"]

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
            if not sale.invoice_pdf:
                generate_sale_invoice_pdf(sale)
                sale.refresh_from_db()
            if not sale.invoice_pdf:
                return Response({DETAILS: "Factura PDF no disponible."}, status=status.HTTP_404_NOT_FOUND)
            return FileResponse(sale.invoice_pdf.open("rb"), as_attachment=True, filename=sale.invoice_pdf.name.split("/")[-1])
        except Exception as e:
            logging.error(f"[sale_viewset - download_invoice] Error descargando factura de venta {pk}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], url_path="invoice/regenerate")
    def regenerate_invoice(self, request, pk=None):
        try:
            sale = self.get_object()
            generate_sale_invoice_pdf(sale)
            sale.refresh_from_db()
            serializer = self.get_serializer(sale)
            return Response({MESSAGE: "Factura regenerada correctamente.", "sale": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            logging.error(f"[sale_viewset - regenerate_invoice] Error regenerando factura de venta {pk}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get"], url_path="economic-summary")
    def economic_summary(self, request):
        try:
            company = resolve_user_company(request.user)
            if not company:
                return Response({DETAILS: "Empresa no encontrada."}, status=status.HTTP_404_NOT_FOUND)

            collections_qs = company_collection_cost_queryset(company)
            sales_qs = Sale.objects.filter(company=company)

            total_cost = collections_qs.aggregate(total=Sum("total_price")).get("total") or 0
            total_income = sales_qs.aggregate(total=Sum("total")).get("total") or 0
            total_bought_volume = collections_qs.aggregate(total=Sum("net_liters")).get("total") or 0
            total_sold_volume = sales_qs.aggregate(total=Sum("quantity")).get("total") or 0

            monthly = []
            for year, month in _monthly_keys():
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
        except Exception as e:
            logging.error(f"[sale_viewset - economic_summary] Error obteniendo resumen economico: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

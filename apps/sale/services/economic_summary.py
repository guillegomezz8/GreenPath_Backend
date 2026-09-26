from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.base.unit_conversion import QuantityConverter
from apps.bulk_collection.models import BulkCollection
from apps.company.utils import get_or_create_company_settings
from apps.sale.models import Sale, SaleLine
from apps.sale.utils import company_collection_cost_queryset


def _apply_date_range(queryset, field_name, start_date, end_date):
    if start_date and end_date:
        return queryset.filter(**{f"{field_name}__range": (start_date, end_date)})
    return queryset


def _sum(queryset, field_name):
    return queryset.aggregate(total=Sum(field_name)).get("total") or Decimal("0.00")


def _filter_month(queryset, field_name, year, month):
    return queryset.filter(
        **{
            f"{field_name}__year": year,
            f"{field_name}__month": month,
        }
    )


def _monthly_keys(start_date=None, end_date=None, months=6):
    if start_date and end_date:
        items = []
        year, month = start_date.year, start_date.month
        while (year, month) <= (end_date.year, end_date.month):
            items.append((year, month))
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        return items

    current = timezone.localdate()
    items = []
    for offset in range(months - 1, -1, -1):
        year, month = current.year, current.month - offset
        while month <= 0:
            year, month = year - 1, month + 12
        items.append((year, month))
    return items


def _sale_rows(sales_qs):
    line_rows = list(SaleLine.objects.filter(sale__in=sales_qs).values("sale_id", "unit", "quantity"))
    sales_with_lines = {row["sale_id"] for row in line_rows}
    fallback_rows = list(sales_qs.exclude(id__in=sales_with_lines).values("unit", "quantity"))
    return line_rows + fallback_rows


def _quantity_summary(converter, collection_qs, bulk_qs, sales_qs):
    collection_liters = _sum(collection_qs, "measured_liters")
    bulk_liters, ignored_bulk = converter.aggregate_as_liters(bulk_qs.values("unit", "quantity"))
    sold_liters, ignored_sales = converter.aggregate_as_liters(_sale_rows(sales_qs))
    return {
        "bought": converter.from_liters(collection_liters + bulk_liters),
        "sold": converter.from_liters(sold_liters),
        "ignored": {"bulk_collections": ignored_bulk, "sales": ignored_sales},
    }


def _period_summary(converter, collection_qs, bulk_qs, sales_qs):
    income = _sum(sales_qs, "total")
    collection_cost = _sum(collection_qs, "total_price")
    bulk_collection_cost = _sum(bulk_qs.filter(billable=True), "total_price")
    total_cost = collection_cost + bulk_collection_cost

    return {
        "income": income,
        "collection_cost": collection_cost,
        "bulk_collection_cost": bulk_collection_cost,
        "total_cost": total_cost,
        "profit": income - total_cost,
        "quantities": _quantity_summary(converter, collection_qs, bulk_qs, sales_qs),
    }


def _monthly_summary(converter, collections_qs, bulk_qs, sales_qs, year, month):
    period = _period_summary(
        converter,
        _filter_month(collections_qs, "collection_date", year, month),
        _filter_month(bulk_qs, "collection_date", year, month),
        _filter_month(sales_qs, "invoice_date", year, month),
    )
    quantities = period["quantities"]
    return {
        "year": year,
        "month": month,
        "income": period["income"],
        "cost": period["total_cost"],
        "profit": period["profit"],
        "bought_quantities": quantities["bought"],
        "sold_quantities": quantities["sold"],
        "ignored_quantities": quantities["ignored"],
    }


def build_economic_summary(company, start_date=None, end_date=None):
    settings_obj = get_or_create_company_settings(company)
    converter = QuantityConverter(settings_obj.oil_density_kg_per_liter)
    collections_qs = _apply_date_range(company_collection_cost_queryset(company), "collection_date", start_date, end_date)
    sales_qs = _apply_date_range(Sale.objects.filter(company=company), "invoice_date", start_date, end_date)
    bulk_qs = _apply_date_range(BulkCollection.objects.filter(company=company), "collection_date", start_date, end_date)
    period = _period_summary(converter, collections_qs, bulk_qs, sales_qs)
    quantities = period["quantities"]
    monthly = [
        _monthly_summary(converter, collections_qs, bulk_qs, sales_qs, year, month)
        for year, month in _monthly_keys(start_date, end_date)
    ]

    return {
        "total_cost": period["total_cost"],
        "total_income": period["income"],
        "net_profit": period["profit"],
        "bought_quantities": quantities["bought"],
        "sold_quantities": quantities["sold"],
        "total_bought_volume": quantities["bought"]["L"],
        "total_sold_volume": quantities["sold"]["L"],
        "bulk_collection_cost": period["bulk_collection_cost"],
        "ignored_quantities": quantities["ignored"],
        "conversion": {
            "base_unit": "L",
            "oil_density_kg_per_liter": settings_obj.oil_density_kg_per_liter,
        },
        "monthly": monthly,
    }

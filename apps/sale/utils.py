import io
import logging
import math
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models, transaction
from django.template.loader import render_to_string
from django.utils import timezone

from apps.base.enums import CollectionStatus
from apps.base.logger import configure_logging
from apps.collection.models import Collection
from apps.company.utils import get_or_create_company_settings
from apps.sale.models import Sale

configure_logging()
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
logging.getLogger("fontTools.ttLib").setLevel(logging.WARNING)
logging.getLogger("fontTools.ttLib.tables").setLevel(logging.WARNING)
logging.getLogger("weasyprint").setLevel(logging.WARNING)
logging.getLogger("weasyprint.progress").setLevel(logging.WARNING)


def assign_sale_invoice_number(sale):
    invoice_date = sale.invoice_date or sale.sale_date
    invoice_year = invoice_date.year

    with transaction.atomic():
        last_sale = (
            Sale.objects.select_for_update()
            .filter(company=sale.company, invoice_year=invoice_year)
            .order_by("-invoice_sequence")
            .first()
        )
        next_sequence = 1 if not last_sale or not last_sale.invoice_sequence else last_sale.invoice_sequence + 1

    sale.invoice_year = invoice_year
    sale.invoice_sequence = next_sequence
    sale.invoice_number = f"{next_sequence:03d}/{invoice_year}"
    return sale


def _billing_address_lines(settings_obj):
    lines = [settings_obj.billing_address]
    locality_parts = [value for value in [settings_obj.billing_postal_code, settings_obj.billing_city] if value]
    locality = " ".join(locality_parts)
    if settings_obj.billing_province:
        locality = f"{locality}, {settings_obj.billing_province}" if locality else settings_obj.billing_province
    if locality:
        lines.append(locality)
    if settings_obj.billing_country:
        lines.append(settings_obj.billing_country)
    return [value for value in lines if value]


def _buyer_address_lines(buyer):
    lines = [buyer.fiscal_address]
    locality_parts = [value for value in [buyer.postal_code, buyer.city] if value]
    locality = " ".join(locality_parts)
    if buyer.province:
        locality = f"{locality}, {buyer.province}" if locality else buyer.province
    if locality:
        lines.append(locality)
    if buyer.country:
        lines.append(buyer.country)
    return [value for value in lines if value]


def _format_money(value, currency="EUR", decimals=2):
    quantizer = Decimal("1").scaleb(-decimals)
    amount = Decimal(value or Decimal("0.00")).quantize(quantizer, rounding=ROUND_HALF_UP)
    symbol = "\u20ac" if currency == "EUR" else currency
    raw = f"{amount:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{raw} {symbol}".strip()



def _format_decimal(value, suffix="", decimals=2):
    quantizer = Decimal("1").scaleb(-decimals)
    amount = Decimal(value or Decimal("0.00")).quantize(quantizer, rounding=ROUND_HALF_UP)
    raw = f"{amount:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{raw}{suffix}".strip()


def _file_uri(file_field):
    if not file_field:
        return None
    try:
        return Path(file_field.path).resolve().as_uri()
    except Exception:
        return None


def _get_empty_rows(product_description):
    description = (product_description or "").strip()
    estimated_lines = max(1, math.ceil(len(description) / 52))
    row_count = max(8, 12 - estimated_lines)
    return range(row_count)


def _invoice_file_name(sale):
    invoice_number = (sale.invoice_number or "").strip()
    invoice_year = sale.invoice_year or sale.invoice_date.year
    cleaned_number = re.sub(r"[^A-Za-z0-9]+", "-", invoice_number).strip("-")
    if not cleaned_number:
        cleaned_number = f"sale-{sale.id or 'draft'}"
    return f"{invoice_year}/FACTURA_{cleaned_number}.pdf"


def _invoice_template_context(sale, settings_obj):
    company_city_line = " ".join(
        [value for value in [settings_obj.billing_postal_code, settings_obj.billing_city] if value]
    )
    if settings_obj.billing_province:
        company_city_line = (
            f"{company_city_line}, {settings_obj.billing_province}"
            if company_city_line else settings_obj.billing_province
        )

    buyer_city_line = " ".join([value for value in [sale.buyer.postal_code, sale.buyer.city] if value])
    if sale.buyer.province:
        buyer_city_line = f"{buyer_city_line}, {sale.buyer.province}" if buyer_city_line else sale.buyer.province

    items = [
        {
            "cantidad": f"{_format_decimal(sale.quantity, decimals=0)} {sale.unit}".strip(),
            "descripcion": sale.product_description,
            "precio_unitario": _format_money(sale.unit_price, sale.currency, decimals=3),
            "total": _format_money(sale.subtotal, sale.currency),
        }
    ]

    return {
        "numero_factura": sale.invoice_number,
        "fecha_factura": sale.invoice_date.strftime("%d/%m/%Y"),
        "empresa_nombre": settings_obj.billing_business_name or sale.company.name,
        "empresa_cif": settings_obj.billing_tax_id,
        "empresa_direccion": settings_obj.billing_address,
        "empresa_ciudad": company_city_line,
        "empresa_telefono": settings_obj.billing_phone,
        "empresa_email": settings_obj.billing_email,
        "codigo_ler": settings_obj.billing_ler_code,
        "cliente_nombre": sale.buyer.fiscal_name,
        "cliente_cif": sale.buyer.tax_id,
        "cliente_direccion": sale.buyer.fiscal_address,
        "cliente_ciudad": buyer_city_line,
        "cuenta_bancaria": settings_obj.billing_bank_account,
        "base_imponible": _format_money(sale.subtotal, sale.currency),
        "iva_porcentaje": _format_decimal(sale.tax_rate),
        "iva_cantidad": _format_money(sale.tax_amount, sale.currency),
        "items": items,
        "total": _format_money(sale.total, sale.currency),
        "company_name": settings_obj.billing_business_name or sale.company.name,
        "company_tax_id": settings_obj.billing_tax_id,
        "company_address": settings_obj.billing_address,
        "company_postal_code": settings_obj.billing_postal_code,
        "company_city": settings_obj.billing_city,
        "company_province": settings_obj.billing_province,
        "company_country": settings_obj.billing_country,
        "company_address_lines": _billing_address_lines(settings_obj),
        "company_phone": settings_obj.billing_phone,
        "company_email": settings_obj.billing_email,
        "company_bank_account": settings_obj.billing_bank_account,
        "company_ler_code": settings_obj.billing_ler_code,
        "company_footer": settings_obj.billing_footer,
        "company_logo_uri": _file_uri(settings_obj.billing_logo),
        "buyer_name": sale.buyer.fiscal_name,
        "buyer_tax_id": sale.buyer.tax_id,
        "buyer_address": sale.buyer.fiscal_address,
        "buyer_postal_code": sale.buyer.postal_code,
        "buyer_city": sale.buyer.city,
        "buyer_province": sale.buyer.province,
        "buyer_country": sale.buyer.country,
        "buyer_contact_person": sale.buyer.contact_person,
        "buyer_address_lines": _buyer_address_lines(sale.buyer),
        "buyer_email": sale.buyer.email,
        "buyer_phone": sale.buyer.phone,
        "invoice_number": sale.invoice_number,
        "invoice_date": sale.invoice_date.strftime("%d/%m/%Y"),
        "sale_date": sale.sale_date.strftime("%d/%m/%Y"),
        "quantity_label": f"{_format_decimal(sale.quantity, decimals=0)} {sale.unit}".strip(),
        "quantity": _format_decimal(sale.quantity, decimals=0),
        "product_description": sale.product_description,
        "unit_price": _format_money(sale.unit_price, sale.currency, decimals=3),
        "subtotal": _format_money(sale.subtotal, sale.currency),
        "tax_rate": _format_decimal(sale.tax_rate),
        "tax_amount": _format_money(sale.tax_amount, sale.currency),
        "total_label": "TOTAL EUROS" if sale.currency == "EUR" else f"TOTAL {sale.currency}",
        "currency": sale.currency,
        "notes": sale.notes,
        "empty_rows": _get_empty_rows(sale.product_description),
    }


def generate_sale_invoice_pdf(sale):
    try:
        from weasyprint import HTML
    except Exception as e:
        logging.error(f"[sale_utils - generate_sale_invoice_pdf] WeasyPrint no disponible para venta {sale.id}: {str(e)}")
        raise ValueError("La libreria de PDF no esta disponible. Debes instalar weasyprint.")

    settings_obj = get_or_create_company_settings(sale.company)
    html_content = render_to_string(
        "sale/invoice.html",
        _invoice_template_context(sale, settings_obj),
    )
    buffer = io.BytesIO()
    HTML(string=html_content, base_url=str(Path(__file__).resolve().parents[2])).write_pdf(buffer)
    buffer.seek(0)

    filename = _invoice_file_name(sale)
    sale.invoice_pdf.save(filename, ContentFile(buffer.getvalue()), save=False)
    sale.invoice_generated_at = timezone.now()
    sale.save(update_fields=["invoice_pdf", "invoice_generated_at", "modified_date"])
    return sale


def company_collection_cost_queryset(company):
    return (
        Collection.objects
        .filter(status=CollectionStatus.CONFIRMED, billable=True)
        .filter(
            models.Q(client__companies__id=company.id) |
            models.Q(worker__company_id=company.id) |
            models.Q(route_day_client__route_day__route__company_id=company.id)
        )
        .distinct()
    )

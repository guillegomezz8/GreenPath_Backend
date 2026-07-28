from datetime import date
from decimal import Decimal

from django.template.loader import render_to_string
from django.test import TestCase

from apps.base.test_utils import BackendTestMixin
from apps.sale.models import Sale, SaleLine
from apps.sale.utils import _invoice_template_context


class SaleUtilsTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("sale-utils")

    def test_invoice_template_splits_long_buyer_address_into_multiple_lines(self):
        buyer = self.create_buyer(
            self.company,
            fiscal_name="RECICLADOS PAR S.L.",
            tax_id="B55555555",
        )
        buyer.fiscal_address = "Poligono Industrial Principe Felipe, C/ Toledo num. 1, Nave 2, Buzon 19"
        buyer.postal_code = "41000"
        buyer.city = "Sevilla"
        buyer.province = "Sevilla"
        buyer.country = "Espana"
        buyer.save()

        sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            sale_date=date(2026, 4, 8),
            invoice_date=date(2026, 4, 8),
            invoice_number="006/2026",
            product_description="Venta puntual",
            quantity=Decimal("100.00"),
            unit="L",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )

        context = _invoice_template_context(sale, self.company.settings)
        html = render_to_string("sale/invoice.html", context)

        self.assertEqual(context["buyer_address_lines"][0], "Poligono Industrial Principe Felipe")
        self.assertEqual(context["buyer_address_lines"][1], "C/ Toledo num. 1, Nave 2, Buzon 19")
        self.assertIn(">Poligono Industrial Principe Felipe<", html)
        self.assertIn(">C/ Toledo num. 1, Nave 2, Buzon 19<", html)
        self.assertNotIn(
            "Poligono Industrial Principe Felipe, C/ Toledo num. 1, Nave 2, Buzon 19",
            html,
        )

    def test_invoice_template_contains_all_sale_lines_and_tax_rates(self):
        buyer = self.create_buyer(
            self.company,
            fiscal_name="COMPRADOR MULTILINEA S.L.",
            tax_id="B56565656",
        )
        sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            sale_date=date(2026, 7, 9),
            invoice_date=date(2026, 7, 9),
            invoice_number="021/2026",
            product_description="Temporal",
            quantity=Decimal("1.00"),
            unit="ud",
            unit_price=Decimal("1.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        first_line = SaleLine(
            sale=sale,
            position=0,
            product_description="Aceite recuperado",
            quantity=Decimal("100.00"),
            unit="kg",
            unit_price=Decimal("1.50"),
            tax_rate=Decimal("21.00"),
        )
        first_line.save(recalculate_sale=False)
        second_line = SaleLine(
            sale=sale,
            position=1,
            product_description="Servicio de transporte",
            quantity=Decimal("2.00"),
            unit="ud",
            unit_price=Decimal("50.00"),
            tax_rate=Decimal("10.00"),
        )
        second_line.save(recalculate_sale=False)
        sale.recalculate_from_lines()

        context = _invoice_template_context(sale, self.company.settings)
        html = render_to_string("sale/invoice.html", context)

        self.assertEqual(len(context["items"]), 2)
        self.assertEqual(len(context["tax_breakdown"]), 2)
        self.assertIn("Aceite recuperado", html)
        self.assertIn("Servicio de transporte", html)
        self.assertIn("IVA 10,00 %", html)
        self.assertIn("IVA 21,00 %", html)

from datetime import date
from decimal import Decimal

from django.template.loader import render_to_string
from django.test import TestCase

from apps.base.tests.helpers import BackendTestMixin
from apps.sale.models import Sale, SaleInvoiceIssuerSnapshot, SaleLine
from apps.sale.utils import _invoice_template_context, _resolve_sale_invoice_issuer


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

    def test_invoice_template_uses_frozen_company_billing_data(self):
        settings_obj = self.company.settings
        settings_obj.billing_business_name = "Empresa Original S.L."
        settings_obj.billing_tax_id = "B11111111"
        settings_obj.billing_address = "Calle Original 1"
        settings_obj.billing_postal_code = "41001"
        settings_obj.billing_city = "Sevilla"
        settings_obj.billing_province = "Sevilla"
        settings_obj.billing_phone = "955111111"
        settings_obj.billing_email = "original@example.com"
        settings_obj.billing_bank_account = "ES1111111111111111111111"
        settings_obj.save()

        buyer = self.create_buyer(
            self.company,
            fiscal_name="COMPRADOR FOTO S.L.",
            tax_id="B57575757",
        )
        sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            sale_date=date(2026, 8, 1),
            invoice_date=date(2026, 8, 1),
            invoice_number="030/2026",
            product_description="Aceite original",
            quantity=Decimal("10.00"),
            unit="kg",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        first_snapshot_id = sale.invoice_issuer_id

        settings_obj.billing_business_name = "Empresa Nueva S.L."
        settings_obj.billing_bank_account = "ES2222222222222222222222"
        settings_obj.save()

        sale.refresh_from_db()
        context = _invoice_template_context(sale, sale.invoice_issuer)

        self.assertEqual(context["empresa_nombre"], "Empresa Original S.L.")
        self.assertEqual(context["cuenta_bancaria"], "ES1111111111111111111111")

        second_sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            sale_date=date(2026, 8, 2),
            invoice_date=date(2026, 8, 2),
            invoice_number="031/2026",
            product_description="Aceite nuevo",
            quantity=Decimal("10.00"),
            unit="kg",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )

        self.assertNotEqual(second_sale.invoice_issuer_id, first_snapshot_id)
        self.assertEqual(second_sale.invoice_issuer.billing_bank_account, "ES2222222222222222222222")
        self.assertEqual(SaleInvoiceIssuerSnapshot.objects.count(), 2)

    def test_invoice_download_does_not_assign_missing_invoice_issuer(self):
        buyer = self.create_buyer(
            self.company,
            fiscal_name="COMPRADOR SIN FOTO S.L.",
            tax_id="B58585858",
        )
        sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            sale_date=date(2026, 8, 3),
            invoice_date=date(2026, 8, 3),
            invoice_number="032/2026",
            product_description="Aceite sin foto",
            quantity=Decimal("10.00"),
            unit="kg",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        Sale.objects.filter(pk=sale.pk).update(invoice_issuer=None)
        sale.refresh_from_db()

        with self.assertRaisesMessage(
            ValueError,
            "La venta no tiene datos fiscales de factura asociados.",
        ):
            _resolve_sale_invoice_issuer(sale)

        sale.refresh_from_db()
        self.assertIsNone(sale.invoice_issuer_id)

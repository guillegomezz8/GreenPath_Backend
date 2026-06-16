from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.base.test_utils import BackendTestMixin
from apps.sale.models import Sale


class BuyerAndSaleApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("sale")
        self.worker_user, self.worker = self.create_worker(self.company, "sale-worker")
        self.owner_client = self.api_client_for(self.owner_user)
        self.worker_client = self.api_client_for(self.worker_user)

    def test_owner_can_create_buyer_for_own_company(self):
        response = self.owner_client.post(
            "/buyers/",
            {
                "fiscal_name": "Comprador Uno",
                "tax_id": "B11111111",
                "fiscal_address": "Calle Factura 1",
                "postal_code": "41001",
                "city": "Sevilla",
                "province": "Sevilla",
                "country": "Espana",
                "email": "comprador1@example.com",
                "phone": "600123123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["company_name"], self.company.name)

    def test_owner_can_create_sale_with_manual_invoice_number(self):
        buyer = self.create_buyer(self.company, "Comprador Venta", "B22222222")

        response = self.owner_client.post(
            "/sales/",
            {
                "buyer": buyer.id,
                "invoice_number": "004/2026",
                "invoice_date": "2026-03-24",
                "product_description": "Venta de aceite usado tratado",
                "quantity": "120.00",
                "unit": "L",
                "unit_price": "0.82",
                "tax_rate": "21.00",
                "currency": "EUR",
                "notes": "Venta demo",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        sale = Sale.objects.get(company=self.company, invoice_number="004/2026")
        self.assertEqual(sale.invoice_date.isoformat(), "2026-03-24")
        self.assertEqual(sale.sale_date.isoformat(), "2026-03-24")
        self.assertEqual(sale.subtotal, Decimal("98.40"))
        self.assertEqual(sale.tax_amount, Decimal("20.66"))
        self.assertEqual(sale.total, Decimal("119.06"))
        self.assertFalse(bool(sale.invoice_pdf))
        self.assertIsNone(sale.invoice_generated_at)

    @patch("apps.sale.api.viewsets.sale_viewset.generate_sale_invoice_pdf")
    def test_download_invoice_generates_pdf_on_demand_without_storing_file(self, generate_pdf_mock):
        buyer = self.create_buyer(self.company, "Comprador PDF", "B33333333")
        sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            invoice_number="005/2026",
            invoice_date=date(2026, 3, 25),
            product_description="Venta puntual de aceite",
            quantity=Decimal("50.00"),
            unit="L",
            unit_price=Decimal("1.10"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        generate_pdf_mock.return_value = (b"%PDF-demo", "FACTURA_005-2026.pdf")

        response = self.owner_client.get(f"/sales/{sale.id}/invoice/download/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('filename="FACTURA_005-2026.pdf"', response["Content-Disposition"])
        generate_pdf_mock.assert_called_once_with(sale)
        sale.refresh_from_db()
        self.assertFalse(bool(sale.invoice_pdf))
        self.assertIsNone(sale.invoice_generated_at)

    def test_worker_cannot_access_buyers(self):
        response = self.worker_client.get("/buyers/")

        self.assertEqual(response.status_code, 403)

    def test_owner_can_filter_sales_list_by_date_range(self):
        buyer = self.create_buyer(self.company, "Comprador Rango", "B44444444")
        Sale.objects.create(
            company=self.company,
            buyer=buyer,
            invoice_number="010/2026",
            invoice_date=date(2026, 1, 15),
            product_description="Venta enero",
            quantity=Decimal("40.00"),
            unit="L",
            unit_price=Decimal("1.50"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        included_sale = Sale.objects.create(
            company=self.company,
            buyer=buyer,
            invoice_number="011/2026",
            invoice_date=date(2026, 3, 10),
            product_description="Venta marzo",
            quantity=Decimal("60.00"),
            unit="L",
            unit_price=Decimal("1.80"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )

        response = self.owner_client.get("/sales/", {"start_date": "2026-03-01", "end_date": "2026-03-31"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], included_sale.id)

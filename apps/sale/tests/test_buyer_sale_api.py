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

    @patch("apps.sale.api.serializers.sale_serializers.generate_sale_invoice_pdf")
    def test_owner_can_create_sale_with_manual_invoice_number(self, generate_pdf_mock):
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
        generate_pdf_mock.assert_called_once_with(sale)

    def test_worker_cannot_access_buyers(self):
        response = self.worker_client.get("/buyers/")

        self.assertEqual(response.status_code, 403)

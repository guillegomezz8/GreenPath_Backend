from decimal import Decimal
from types import SimpleNamespace

from django.contrib import admin
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from apps.base.tests.helpers import BackendTestMixin
from apps.bulk_collection.admin import BulkCollectionAdmin
from apps.bulk_collection.models import BulkCollection
from apps.company.models import CompanySettings


class BulkCollectionApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, _, self.company = self.create_owner_context("bulk")
        self.worker_user, _ = self.create_worker(self.company, "bulk-worker")
        _, self.client_profile = self.create_client(self.company, "bulk-client")
        self.api = self.api_client_for(self.owner_user)

    def test_quantity_and_unit_price_calculate_total(self):
        response = self.api.post(
            "/bulk-collections/",
            {
                "client": self.client_profile.id,
                "collection_date": "2026-09-24",
                "unit": "KG",
                "calculation_mode": "TOTAL",
                "quantity": "125.50",
                "unit_price": "0.8000",
                "billable": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bulk_collection = BulkCollection.objects.get(id=response.data["id"])
        self.assertEqual(bulk_collection.company, self.company)
        self.assertEqual(bulk_collection.total_price, Decimal("100.40"))

    def test_quantity_and_total_calculate_unit_price(self):
        response = self.api.post(
            "/bulk-collections/",
            {
                "client": self.client_profile.id,
                "collection_date": "2026-09-24",
                "unit": "L",
                "calculation_mode": "UNIT_PRICE",
                "quantity": "80.00",
                "total_price": "100.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["unit_price"]), Decimal("1.2500"))

    def test_unit_price_and_total_calculate_quantity(self):
        response = self.api.post(
            "/bulk-collections/",
            {
                "client": self.client_profile.id,
                "collection_date": "2026-09-24",
                "unit": "UD",
                "calculation_mode": "QUANTITY",
                "unit_price": "2.5000",
                "total_price": "50.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Decimal(response.data["quantity"]), Decimal("20.00"))

    def test_bulk_collection_isolated_by_company_and_owner_only(self):
        other_owner, _, other_company = self.create_owner_context("bulk-other")
        _, other_client = self.create_client(other_company, "bulk-other-client")
        BulkCollection.objects.create(
            company=other_company,
            client=other_client,
            collection_date="2026-09-24",
            unit="KG",
            calculation_mode="TOTAL",
            quantity=Decimal("10.00"),
            unit_price=Decimal("2.0000"),
        )

        list_response = self.api.get("/bulk-collections/")
        worker_response = self.api_client_for(self.worker_user).get("/bulk-collections/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 0)
        self.assertEqual(worker_response.status_code, status.HTTP_403_FORBIDDEN)

        other_response = self.api_client_for(other_owner).get("/bulk-collections/")
        self.assertEqual(other_response.data["count"], 1)

    def test_rejects_client_from_another_company(self):
        _, _, other_company = self.create_owner_context("foreign-client")
        _, other_client = self.create_client(other_company, "foreign-client-profile")

        response = self.api.post(
            "/bulk-collections/",
            {
                "client": other_client.id,
                "collection_date": "2026-09-24",
                "unit": "L",
                "calculation_mode": "TOTAL",
                "quantity": "10.00",
                "unit_price": "1.0000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_module_can_be_disabled_per_company(self):
        self.company.settings.bulk_collections_enabled = False
        self.company.settings.save()

        response = self.api.get("/bulk-collections/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_module_is_hidden_when_disabled_for_every_company(self):
        request = SimpleNamespace(
            user=SimpleNamespace(has_module_perms=lambda app_label: True),
        )
        model_admin = BulkCollectionAdmin(BulkCollection, admin.site)
        CompanySettings.objects.update(bulk_collections_enabled=False)

        self.assertFalse(model_admin.has_module_permission(request))

        self.company.settings.bulk_collections_enabled = True
        self.company.settings.save(update_fields=["bulk_collections_enabled"])
        self.assertTrue(model_admin.has_module_permission(request))

    def test_accepts_invoice_attachment(self):
        invoice = SimpleUploadedFile("factura.pdf", b"%PDF-1.4 demo", content_type="application/pdf")

        response = self.api.post(
            "/bulk-collections/",
            {
                "client": self.client_profile.id,
                "collection_date": "2026-09-24",
                "unit": "KG",
                "calculation_mode": "TOTAL",
                "quantity": "10.00",
                "unit_price": "2.0000",
                "billable": "true",
                "invoice_file": invoice,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bulk_collection = BulkCollection.objects.get(id=response.data["id"])
        self.assertTrue(bulk_collection.invoice_file.name)
        bulk_collection.invoice_file.delete(save=False)

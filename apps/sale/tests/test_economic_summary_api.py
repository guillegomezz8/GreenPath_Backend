from datetime import date
from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.enums import CollectionStatus, ContainerType, Role
from apps.collection.models import Collection
from apps.company.models import Company
from apps.sale.models import Buyer, Sale
from apps.user.models.client import Client
from apps.user.models.user import User
from apps.user.models.worker import Worker


class SaleEconomicSummaryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = Company.objects.create(name="GreenPath Sales Test")

        self.owner_user = User.objects.create_user(
            username="owner_sales",
            email="owner_sales@example.com",
            password="password123",
        )
        self.owner_worker = Worker.objects.create(
            user=self.owner_user,
            company=self.company,
            role=Role.OWNER,
            name="Owner",
            surname="Sales",
            address="Calle Owner 10",
            phone="600000010",
            dni="10101010A",
        )
        self.company.owner = self.owner_user
        self.company.save()

        self.worker_user = User.objects.create_user(
            username="worker_sales",
            email="worker_sales@example.com",
            password="password123",
        )
        self.worker_profile = Worker.objects.create(
            user=self.worker_user,
            company=self.company,
            role=Role.WORKER,
            name="Worker",
            surname="Sales",
            address="Calle Worker 11",
            phone="600000011",
            dni="11111111B",
        )

        self.client_user = User.objects.create_user(
            username="client_sales",
            email="client_sales@example.com",
            password="password123",
        )
        self.client_profile = Client.objects.create(
            user=self.client_user,
            name="Cliente Demo",
            phone="600000012",
            cif="B12345678",
            address="Calle Cliente 12",
            city="Sevilla",
            postal_code="41001",
            country="Espana",
        )
        self.client_profile.companies.add(self.company)

        self.buyer = Buyer.objects.create(
            company=self.company,
            fiscal_name="Comprador Demo",
            tax_id="B87654321",
            fiscal_address="Calle Factura 1",
            postal_code="41002",
            city="Sevilla",
            province="Sevilla",
            country="Espana",
        )

    def authenticate_owner(self):
        self.client.force_authenticate(user=self.owner_user)

    def authenticate_worker(self):
        self.client.force_authenticate(user=self.worker_user)

    def test_economic_summary_counts_only_confirmed_and_billable_collections(self):
        today = date.today()

        Sale.objects.create(
            company=self.company,
            buyer=self.buyer,
            sale_date=today,
            invoice_date=today,
            invoice_number="001/2026",
            product_description="Venta de aceite tratado",
            quantity=Decimal("100.00"),
            unit="L",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
        )

        Collection.objects.create(
            client=self.client_profile,
            worker=self.worker_profile,
            collection_date=today,
            container_type=ContainerType.BIDONES,
            container_number=2,
            measured_liters=Decimal("100.00"),
            deduction_liters=Decimal("10.00"),
            price_per_liter=Decimal("1.00"),
            billable=True,
            status=CollectionStatus.CONFIRMED,
        )
        Collection.objects.create(
            client=self.client_profile,
            worker=self.worker_profile,
            collection_date=today,
            container_type=ContainerType.BIDONES,
            container_number=1,
            measured_liters=Decimal("50.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            billable=False,
            status=CollectionStatus.CONFIRMED,
        )
        Collection.objects.create(
            client=self.client_profile,
            worker=self.worker_profile,
            collection_date=today,
            container_type=ContainerType.BIDONES,
            container_number=1,
            measured_liters=Decimal("30.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            billable=True,
            status=CollectionStatus.CANCELED,
        )

        self.authenticate_owner()
        response = self.client.get("/sales/economic-summary/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_cost"], Decimal("90.00"))
        self.assertEqual(response.data["total_income"], Decimal("242.00"))
        self.assertEqual(response.data["net_profit"], Decimal("152.00"))
        self.assertEqual(response.data["total_bought_volume"], Decimal("90.00"))
        self.assertEqual(response.data["total_sold_volume"], Decimal("100.00"))
        self.assertTrue(
            any(
                month["income"] == Decimal("242.00") and month["cost"] == Decimal("90.00")
                for month in response.data["monthly"]
            )
        )

    def test_worker_cannot_access_economic_summary(self):
        self.authenticate_worker()

        response = self.client.get("/sales/economic-summary/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from decimal import Decimal

from django.test import TestCase

from apps.base.enums import CollectionStatus, PickupFrequency
from apps.base.test_utils import BackendTestMixin
from apps.collection.models import Collection


class ClientApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("client")
        self.owner_client = self.api_client_for(self.owner_user)
        self.client_user, self.client_profile = self.create_client(self.company, "client-self")
        self.client_api = self.api_client_for(self.client_user)

    def test_owner_list_includes_frequency_counts(self):
        self.create_client(self.company, "weekly-client", frequency=PickupFrequency.WEEKLY)
        self.create_client(self.company, "two-weeks-client", frequency=PickupFrequency.TWO_WEEKS)

        response = self.owner_client.get("/clients/")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data["counts"]["every_week"], 2)
        self.assertGreaterEqual(response.data["counts"]["every_2_weeks"], 1)

    def test_client_historial_counts_only_confirmed_and_billable_paid_amount(self):
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("120.00"),
            deduction_liters=Decimal("20.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("80.00"),
            deduction_liters=Decimal("10.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=False,
        )
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("50.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CANCELED,
            billable=True,
        )

        response = self.client_api.get(f"/clients/historial/{self.client_profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["total_paid"]), Decimal("100.00"))
        self.assertEqual(response.data["stats"]["confirmed_collections"], 2)
        self.assertEqual(response.data["stats"]["canceled_collections"], 1)

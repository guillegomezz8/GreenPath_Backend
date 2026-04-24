from decimal import Decimal

from django.test import TestCase

from apps.base.enums import CollectionStatus, PickupFrequency
from apps.base.test_utils import BackendTestMixin
from apps.collection.models import Collection
from apps.user.models.client import Client
from apps.user.models.user import User


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

    def test_owner_can_create_client_without_email_username_or_cif_when_access_is_disabled(self):
        response = self.owner_client.post(
            "/clients/",
            {
                "get_access": False,
                "name": "Bar La Prueba",
                "address": "Calle Real 10",
                "phone": "600123123",
                "cif": "",
                "city": "Sevilla",
                "postal_code": "41001",
                "country": "Espana",
                "frequency": "WEEKLY",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        client = Client.objects.get(name="Bar La Prueba")
        self.assertEqual(client.cif, "")
        self.assertEqual(client.user.username, "bar-la-prueba")
        self.assertEqual(client.user.email, "bar-la-prueba@clients.greenpath.local")
        self.assertFalse(client.user.has_usable_password())
        self.assertEqual(self.owner_client.get(f"/clients/{client.id}/").data["email"], "")

    def test_create_client_requires_email_if_access_is_enabled(self):
        response = self.owner_client.post(
            "/clients/",
            {
                "get_access": True,
                "name": "Cliente Acceso",
                "user": {"username": "", "email": ""},
                "address": "Calle Sol 2",
                "phone": "600123124",
                "cif": "",
                "city": "Sevilla",
                "postal_code": "41002",
                "country": "Espana",
                "frequency": "WEEKLY",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.data)

    def test_generated_client_credentials_are_unique_for_repeated_names(self):
        User.objects.create_user(username="cliente-demo", email="cliente-demo@clients.greenpath.local", password="TestPass123!")

        first_response = self.owner_client.post(
            "/clients/",
            {
                "get_access": False,
                "name": "Cliente Demo",
                "address": "Calle Luna 3",
                "phone": "600123125",
                "city": "Sevilla",
                "postal_code": "41003",
                "country": "Espana",
                "frequency": "WEEKLY",
            },
            format="json",
        )
        second_response = self.owner_client.post(
            "/clients/",
            {
                "get_access": False,
                "name": "Cliente Demo",
                "address": "Calle Luna 4",
                "phone": "600123126",
                "city": "Sevilla",
                "postal_code": "41004",
                "country": "Espana",
                "frequency": "WEEKLY",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        clients = Client.objects.filter(name="Cliente Demo").order_by("id")
        self.assertEqual(clients.count(), 2)
        self.assertEqual(clients[0].user.username, "cliente-demo-2")
        self.assertEqual(clients[0].user.email, "cliente-demo-2@clients.greenpath.local")
        self.assertEqual(clients[1].user.username, "cliente-demo-3")
        self.assertEqual(clients[1].user.email, "cliente-demo-3@clients.greenpath.local")

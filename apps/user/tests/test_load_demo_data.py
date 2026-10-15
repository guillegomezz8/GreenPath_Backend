import json
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.base.tests.helpers import BackendTestMixin
from apps.collection.models import Collection, CollectionRequest
from apps.company.models import Company
from apps.route.models import Route, RouteDay
from apps.sale.models import Sale
from apps.user.management.commands.load_demo_data import FIXTURE_PATH
from apps.user.models.client import Client
from apps.user.models.user import User


class LoadDemoDataTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.existing_user, _, self.existing_company = self.create_owner_context("existing")
        self.existing_password = self.existing_user.password
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.small_path = Path(self.directory.name) / "small.json"
        # Small scenario still exercises the company/owner circular relationship.
        self.small_fixture = {
            "version": 1,
            "records": [record for record in self.fixture["records"]
                        if record["key"] in {"owner", "company", "owner-worker", "settings", "hub"}],
        }
        self.write_small()

    def write_small(self):
        self.small_path.write_text(json.dumps(self.small_fixture), encoding="utf-8")

    def load(self, **kwargs):
        output = StringIO()
        call_command("load_demo_data", fixture=self.small_path, stdout=output, **kwargs)
        return output.getvalue()

    def test_full_fixture_preserves_existing_data_and_can_be_repeated(self):
        output = StringIO()
        call_command("load_demo_data", date=date(2026, 10, 9), stdout=output)
        owner = User.objects.get(username="propietario@demo.com")
        self.assertTrue(owner.check_password("pass12345"))
        self.assertFalse(owner.is_staff)
        self.assertFalse(owner.is_superuser)
        self.assertEqual(owner.role_type, "owner")
        self.assertEqual(Client.objects.count(), 80)
        self.assertEqual(Collection.objects.count(), 1104)
        self.assertEqual(CollectionRequest.objects.count(), 480)
        self.assertEqual(RouteDay.objects.count(), 60)
        self.assertEqual(Sale.objects.count(), 96)
        self.existing_user.refresh_from_db()
        self.existing_company.refresh_from_db()
        self.assertEqual(self.existing_user.password, self.existing_password)
        self.assertEqual(self.existing_company.name, "Empresa Existing")
        before_counts = (User.objects.count(), Collection.objects.count(), Sale.objects.count())
        call_command("load_demo_data", password="DifferentPassword!", stdout=output)
        self.assertEqual(before_counts, (User.objects.count(), Collection.objects.count(), Sale.objects.count()))
        owner.refresh_from_db()
        self.assertTrue(owner.check_password("pass12345"))
        api = self.api_client_for(owner)
        summary = api.get("/sales/economic-summary/")
        self.assertEqual(summary.status_code, 200)
        self.assertGreater(float(summary.data["total_income"]), 0)
        incomes = [float(month["income"]) for month in summary.data["monthly"]]
        self.assertGreater(max(incomes), min(incomes) * 1.5)
        recent = api.get("/collections/", {"page_size": 8}).data["results"]
        self.assertEqual({row["status_code"] for row in recent},
                         {"CONFIRMED", "PENDING_MEASUREMENT", "CANCELED"})
        route = Route.objects.get(name="demo-clientes - Ruta 1")
        response = api.get(f"/routes/{route.pk}/operational-overview/", {"week_start_date": "2026-10-05"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["route_days"])
        # Exercise upgrading a legacy demo row that has no stable marker yet.
        history_record = next(record for record in self.fixture["records"] if record["key"] == "history-1-1")
        history = Collection.objects.get(notes__contains="[demo:demo-clientes:history-1-1]")
        old_date = date(2026, 10, 9) + timedelta(days=history_record["lookup"]["collection_date"]["date_offset"])
        history.collection_date = old_date
        history.notes = history_record["lookup"]["notes"]
        history.save()
        call_command("refresh_demo_data", dry_run=True, stdout=output)
        history.refresh_from_db()
        self.assertEqual(history.notes, history_record["lookup"]["notes"])
        call_command("refresh_demo_data", stdout=output)
        history.refresh_from_db()
        self.assertIn("[demo:demo-clientes:history-1-1]", history.notes)
        self.assertEqual(Collection.objects.count(), 1104)
        call_command("refresh_demo_data", stdout=output)
        self.assertEqual(Collection.objects.count(), 1104)
        self.existing_user.refresh_from_db()
        self.existing_company.refresh_from_db()
        self.assertEqual(self.existing_user.password, self.existing_password)
        self.assertEqual(self.existing_company.name, "Empresa Existing")

    def test_dry_run_leaves_database_unchanged(self):
        counts = (User.objects.count(), Company.objects.count())
        output = self.load(dry_run=True)
        self.assertIn("sin guardar", output)
        self.assertEqual(counts, (User.objects.count(), Company.objects.count()))

    def test_late_collision_rolls_back_all_created_records(self):
        self.small_fixture["records"].append({
            "key": "collision", "model": "user.user",
            "fields": {"username": "owner-existing", "email": "other@example.com"},
        })
        self.write_small()
        with self.assertRaises(CommandError):
            self.load()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Company.objects.count(), 1)
        self.assertFalse(User.objects.filter(username="propietario@demo.com").exists())

    def test_existing_demo_username_is_not_adopted_or_changed(self):
        collision = self.create_user("propietario@demo.com", "real-person@example.com")
        password = collision.password
        with self.assertRaises(CommandError):
            self.load()
        collision.refresh_from_db()
        self.assertEqual(collision.password, password)
        self.assertEqual(collision.email, "real-person@example.com")

    def test_new_namespace_creates_separate_demo(self):
        self.load()
        self.load(namespace="otra-demo", owner_email="otro@demo.com")
        self.assertEqual(Company.objects.count(), 3)
        self.assertTrue(User.objects.filter(username="otro@demo.com").exists())

    def test_primary_keys_and_numeric_relations_are_rejected(self):
        self.small_fixture["records"][0]["fields"]["id"] = self.existing_user.pk
        self.write_small()
        with self.assertRaises(CommandError):
            self.load()
        del self.small_fixture["records"][0]["fields"]["id"]
        self.small_fixture["records"][2]["fields"]["company"] = self.existing_company.pk
        self.write_small()
        with self.assertRaises(CommandError):
            self.load()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Company.objects.count(), 1)

    def test_custom_owner_credentials_can_log_in(self):
        self.load(owner_email="presentacion@demo.com", password="ClaveElegida123!")
        owner = User.objects.get(username="presentacion@demo.com")
        self.assertEqual(owner.email, "presentacion@demo.com")
        self.assertTrue(owner.check_password("ClaveElegida123!"))
        from rest_framework.test import APIClient
        response = APIClient().post("/login/", {"username": owner.username, "password": "ClaveElegida123!"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_existing_owner_is_not_changed_by_new_credentials(self):
        self.load()
        owner = User.objects.get(username="propietario@demo.com")
        with self.assertRaises(CommandError):
            self.load(owner_email="nuevo@demo.com", password="NuevaClave!")
        owner.refresh_from_db()
        self.assertEqual(owner.username, "propietario@demo.com")
        self.assertEqual(owner.email, "propietario@demo.com")
        self.assertTrue(owner.check_password("pass12345"))

    def test_invalid_email_does_not_create_data(self):
        with self.assertRaises(CommandError):
            self.load(owner_email="no-es-un-email")
        self.assertEqual(Company.objects.count(), 1)

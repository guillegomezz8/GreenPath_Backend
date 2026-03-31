from django.test import TestCase

from apps.base.test_utils import BackendTestMixin
from apps.company.models import CompanyHub


class CompanyApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("company")
        self.worker_user, self.worker = self.create_worker(self.company, "company-worker")
        self.owner_client = self.api_client_for(self.owner_user)
        self.worker_client = self.api_client_for(self.worker_user)

    def test_owner_can_update_company_settings_and_hub(self):
        response = self.owner_client.put(
            "/companies/settings/",
            {
                "default_price_per_liter": "1.450",
                "billing_business_name": "GreenPath Fiscal",
                "billing_tax_id": "B12345678",
                "hub_name": "Nave Central",
                "hub_lat": 37.4001,
                "hub_lng": -6.0012,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.company.refresh_from_db()
        settings_obj = self.company.settings
        hub = CompanyHub.objects.get(company=self.company)

        self.assertEqual(str(settings_obj.default_price_per_liter), "1.450")
        self.assertEqual(settings_obj.billing_business_name, "GreenPath Fiscal")
        self.assertEqual(hub.name, "Nave Central")
        self.assertAlmostEqual(hub.location.y, 37.4001, places=4)
        self.assertAlmostEqual(hub.location.x, -6.0012, places=4)

    def test_worker_can_read_but_not_update_company_settings(self):
        get_response = self.worker_client.get("/companies/settings/")
        put_response = self.worker_client.put(
            "/companies/settings/",
            {"default_price_per_liter": "1.600"},
            format="json",
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(put_response.status_code, 403)

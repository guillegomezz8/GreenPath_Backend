from django.test import TestCase

from apps.base.test_utils import BackendTestMixin


class ZoneApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("zone")
        self.worker_user, self.worker = self.create_worker(self.company, "zone-worker")
        self.owner_client = self.api_client_for(self.owner_user)
        self.worker_client = self.api_client_for(self.worker_user)

    def test_owner_can_create_zone_and_find_it_by_search(self):
        create_response = self.owner_client.post(
            "/zones/",
            {
                "name": "Zona Centro",
                "polygon": "POLYGON((-6.05 37.35, -5.95 37.35, -5.95 37.45, -6.05 37.45, -6.05 37.35))",
            },
            format="json",
        )
        list_response = self.owner_client.get("/zones/?search=Centro")

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["name"], "Zona Centro")

    def test_worker_cannot_create_zone(self):
        response = self.worker_client.post(
            "/zones/",
            {
                "name": "Zona Prohibida",
                "polygon": "POLYGON((-6.05 37.35, -5.95 37.35, -5.95 37.45, -6.05 37.45, -6.05 37.35))",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

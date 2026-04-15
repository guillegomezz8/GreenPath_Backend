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

    def test_owner_list_includes_clients_inside_zone(self):
        zone = self.create_zone(name="Zona Clientes")
        _, inside_client = self.create_client(
            self.company,
            username="inside-zone-client",
            location=self.point_inside_default_polygon(),
        )
        self.create_client(
            self.company,
            username="outside-zone-client",
            location=self.point_outside_default_polygon(),
        )

        response = self.owner_client.get("/zones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        zone_data = response.data["results"][0]
        self.assertEqual(zone_data["name"], zone.name)
        self.assertEqual(zone_data["clients_count"], 1)
        self.assertEqual(len(zone_data["clients"]), 1)
        self.assertEqual(zone_data["clients"][0]["id"], inside_client.id)

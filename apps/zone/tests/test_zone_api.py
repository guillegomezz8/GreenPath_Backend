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
        self.assertEqual(self.company.zones.get().name, "Zona Centro")

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
        zone = self.create_zone(self.company, name="Zona Clientes")
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

    def test_owner_only_sees_zones_from_own_company(self):
        own_zone = self.create_zone(self.company, name="Zona Propia")
        _, _, other_company = self.create_owner_context("zone-other")
        self.create_zone(other_company, name="Zona Ajena")

        response = self.owner_client.get("/zones/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], own_zone.id)

    def test_owner_cannot_access_or_modify_zone_from_other_company(self):
        _, _, other_company = self.create_owner_context("zone-protected")
        other_zone = self.create_zone(other_company, name="Zona Protegida")
        payload = {
            "name": "Zona Manipulada",
            "polygon": "POLYGON((-6.05 37.35, -5.95 37.35, -5.95 37.45, -6.05 37.45, -6.05 37.35))",
        }

        retrieve_response = self.owner_client.get(f"/zones/{other_zone.id}/")
        update_response = self.owner_client.put(f"/zones/{other_zone.id}/", payload, format="json")
        delete_response = self.owner_client.delete(f"/zones/{other_zone.id}/")

        self.assertEqual(retrieve_response.status_code, 404)
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_different_companies_can_use_the_same_zone_name(self):
        other_owner, _, other_company = self.create_owner_context("zone-same-name")
        other_owner_client = self.api_client_for(other_owner)
        payload = {
            "name": "Zona Centro",
            "polygon": "POLYGON((-6.05 37.35, -5.95 37.35, -5.95 37.45, -6.05 37.45, -6.05 37.35))",
        }

        own_response = self.owner_client.post("/zones/", payload, format="json")
        other_response = other_owner_client.post("/zones/", payload, format="json")

        self.assertEqual(own_response.status_code, 201)
        self.assertEqual(other_response.status_code, 201)
        self.assertTrue(self.company.zones.filter(name="Zona Centro").exists())
        self.assertTrue(other_company.zones.filter(name="Zona Centro").exists())

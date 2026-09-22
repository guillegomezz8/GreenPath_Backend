from django.test import TestCase

from apps.base.tests.helpers import BackendTestMixin


class TruckApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("truck")
        self.worker_user, self.worker = self.create_worker(self.company, "truck-driver")
        self.other_worker_user, self.other_worker = self.create_worker(self.company, "truck-other")
        self.owner_client = self.api_client_for(self.owner_user)
        self.worker_client = self.api_client_for(self.worker_user)
        self.old_truck = self.create_truck(self.company, "1111-AAA", driver=self.worker)
        self.new_truck = self.create_truck(self.company, "2222-BBB")

    def test_assign_driver_moves_worker_from_previous_truck(self):
        response = self.owner_client.post(
            f"/trucks/assign-driver/{self.worker.id}/",
            {"truck_id": self.new_truck.id, "force": False},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.old_truck.refresh_from_db()
        self.new_truck.refresh_from_db()

        self.assertIsNone(self.old_truck.driver)
        self.assertEqual(self.new_truck.driver_id, self.worker.id)

    def test_worker_cannot_list_trucks(self):
        response = self.worker_client.get("/trucks/")

        self.assertEqual(response.status_code, 403)

    def test_owner_creates_truck_with_company_inferred_from_profile(self):
        response = self.owner_client.post(
            "/trucks/",
            {
                "registration_number": "3333-CCC",
                "brand": "Mercedes",
                "model": "Atego",
                "year": 2025,
                "capacity": "12000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        created_truck = self.company.trucks.get(registration_number="3333-CCC")
        self.assertEqual(created_truck.company_id, self.company.id)

    def test_owner_cannot_assign_driver_from_another_company_when_creating_truck(self):
        other_company = self.create_company("Empresa Camiones Externa")
        _, external_worker = self.create_worker(other_company, "external-truck-driver")

        response = self.owner_client.post(
            "/trucks/",
            {
                "registration_number": "4444-DDD",
                "driver": external_worker.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.company.trucks.filter(registration_number="4444-DDD").exists())

    def test_owner_updates_truck_without_sending_company(self):
        response = self.owner_client.put(
            f"/trucks/{self.new_truck.id}/",
            {
                "registration_number": self.new_truck.registration_number,
                "brand": "Iveco",
                "model": "Eurocargo",
                "year": 2025,
                "capacity": "15000.00",
                "status": "ACTIVE",
                "fuel": "DIESEL",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.new_truck.refresh_from_db()
        self.assertEqual(self.new_truck.company_id, self.company.id)
        self.assertEqual(self.new_truck.model, "Eurocargo")

from django.test import TestCase

from apps.base.test_utils import BackendTestMixin


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

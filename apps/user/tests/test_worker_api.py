from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.enums import Role
from apps.company.models import Company
from apps.user.models.user import User
from apps.user.models.worker import Worker


class WorkerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.company = Company.objects.create(name="GreenPath Test")
        self.owner_user = User.objects.create_user(
            username="owner_test",
            email="owner_test@example.com",
            password="password123",
        )
        self.owner_worker = Worker.objects.create(
            user=self.owner_user,
            company=self.company,
            role=Role.OWNER,
            name="Owner",
            surname="Principal",
            address="Calle Owner 1",
            phone="600000001",
            dni="11111111A",
        )
        self.company.owner = self.owner_user
        self.company.save()

        self.worker_user = User.objects.create_user(
            username="worker_test",
            email="worker_test@example.com",
            password="password123",
        )
        self.worker_profile = Worker.objects.create(
            user=self.worker_user,
            company=self.company,
            role=Role.WORKER,
            name="Worker",
            surname="Normal",
            address="Calle Worker 2",
            phone="600000002",
            dni="22222222B",
        )

        self.other_company = Company.objects.create(name="Otra Empresa")

    def authenticate_owner(self):
        self.client.force_authenticate(user=self.owner_user)

    def authenticate_worker(self):
        self.client.force_authenticate(user=self.worker_user)

    def build_worker_payload(self, **overrides):
        payload = {
            "get_access": False,
            "user": {
                "username": "nuevo_worker",
                "email": "nuevo_worker@example.com",
            },
            "name": "Nuevo",
            "surname": "Trabajador",
            "address": "Calle Nueva 5",
            "phone": "600000003",
            "dni": "33333333C",
            "birth_date": None,
        }
        payload.update(overrides)
        return payload

    def test_owner_can_create_worker_but_role_is_forced_to_worker(self):
        self.authenticate_owner()

        payload = self.build_worker_payload(role=Role.OWNER, company=self.other_company.id)
        response = self.client.post("/workers/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_worker = Worker.objects.exclude(id__in=[self.owner_worker.id, self.worker_profile.id]).get()
        self.assertEqual(created_worker.role, Role.WORKER)
        self.assertEqual(created_worker.company_id, self.company.id)

    def test_owner_cannot_change_role_of_existing_owner_through_worker_update(self):
        self.authenticate_owner()

        payload = {
            "name": "Owner Editado",
            "surname": self.owner_worker.surname,
            "address": self.owner_worker.address,
            "phone": self.owner_worker.phone,
            "dni": self.owner_worker.dni,
            "email": "owner_editado@example.com",
            "role": Role.WORKER,
        }
        response = self.client.put(f"/workers/{self.owner_worker.id}/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.owner_worker.refresh_from_db()
        self.owner_user.refresh_from_db()
        self.assertEqual(self.owner_worker.role, Role.OWNER)
        self.assertEqual(self.owner_worker.name, "Owner Editado")
        self.assertEqual(self.owner_user.email, "owner_editado@example.com")

    def test_owner_cannot_change_company_of_existing_worker_through_worker_update(self):
        self.authenticate_owner()

        payload = {
            "name": self.worker_profile.name,
            "surname": self.worker_profile.surname,
            "address": self.worker_profile.address,
            "phone": self.worker_profile.phone,
            "dni": self.worker_profile.dni,
            "email": "worker_actualizado@example.com",
            "company": self.other_company.id,
        }
        response = self.client.put(f"/workers/{self.worker_profile.id}/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.worker_profile.refresh_from_db()
        self.worker_user.refresh_from_db()
        self.assertEqual(self.worker_profile.company_id, self.company.id)
        self.assertEqual(self.worker_user.email, "worker_actualizado@example.com")

    def test_worker_cannot_create_workers(self):
        self.authenticate_worker()

        response = self.client.post("/workers/", self.build_worker_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

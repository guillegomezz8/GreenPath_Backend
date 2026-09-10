from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from unittest.mock import patch

from apps.base.tests.helpers import BackendTestMixin


def small_gif(name="avatar.gif"):
    return SimpleUploadedFile(
        name,
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )


class UserProfileApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("profile")
        self.worker_user, self.worker_profile = self.create_worker(self.company, "profile-worker")
        self.client_user, self.client_profile = self.create_client(self.company, "profile-client")
        self.worker_api = self.api_client_for(self.worker_user)
        self.client_api = self.api_client_for(self.client_user)

    def test_worker_can_upload_profile_photo(self):
        response = self.worker_api.put(
            "/users/profile/",
            {"photo": small_gif("worker.gif")},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.worker_profile.refresh_from_db()
        self.assertTrue(self.worker_profile.photo.name.startswith("workers/"))
        self.assertIn("/media/workers/", response.data["profile"]["photo"])

    def test_client_can_upload_profile_photo(self):
        response = self.client_api.put(
            "/users/profile/",
            {"photo": small_gif("client.gif")},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.client_profile.refresh_from_db()
        self.assertTrue(self.client_profile.photo.name.startswith("clients/"))
        self.assertIn("/media/clients/", response.data["profile"]["photo"])

    def test_worker_can_update_extended_profile_fields(self):
        response = self.worker_api.put(
            "/users/profile/",
            {
                "email": "worker-updated@example.com",
                "name": "Trabajador",
                "surname": "Actualizado",
                "phone": "611222333",
                "address": "Calle Perfil 12",
                "dni": "87654321X",
                "birth_date": "1995-05-10",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.worker_user.refresh_from_db()
        self.worker_profile.refresh_from_db()
        self.assertEqual(self.worker_user.email, "worker-updated@example.com")
        self.assertEqual(self.worker_profile.name, "Trabajador")
        self.assertEqual(self.worker_profile.surname, "Actualizado")
        self.assertEqual(self.worker_profile.phone, "611222333")
        self.assertEqual(self.worker_profile.address, "Calle Perfil 12")
        self.assertEqual(self.worker_profile.dni, "87654321X")
        self.assertEqual(self.worker_profile.birth_date.isoformat(), "1995-05-10")
        self.assertEqual(response.data["profile"]["surname"], "Actualizado")

    @patch("apps.user.api.serializers.user_serializers.sync_client_location_from_address")
    def test_client_can_update_extended_profile_fields(self, mock_sync_location):
        response = self.client_api.put(
            "/users/profile/",
            {
                "email": "client-updated@example.com",
                "name": "Cliente Actualizado",
                "phone": "622333444",
                "cif": "B99887766",
                "address": "Avenida Cliente 22",
                "city": "Sevilla",
                "postal_code": "41002",
                "country": "España",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.client_user.refresh_from_db()
        self.client_profile.refresh_from_db()
        self.assertEqual(self.client_user.email, "client-updated@example.com")
        self.assertEqual(self.client_profile.name, "Cliente Actualizado")
        self.assertEqual(self.client_profile.phone, "622333444")
        self.assertEqual(self.client_profile.cif, "B99887766")
        self.assertEqual(self.client_profile.address, "Avenida Cliente 22")
        self.assertEqual(self.client_profile.city, "Sevilla")
        self.assertEqual(self.client_profile.postal_code, "41002")
        self.assertEqual(self.client_profile.country, "España")
        self.assertEqual(response.data["profile"]["cif"], "B99887766")
        mock_sync_location.assert_called_once()

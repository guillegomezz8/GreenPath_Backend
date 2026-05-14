from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.base.test_utils import BackendTestMixin


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

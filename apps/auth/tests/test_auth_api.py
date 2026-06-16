from django.test import TestCase

from apps.base.test_utils import BackendTestMixin


class AuthApiTests(BackendTestMixin, TestCase):
    def test_login_returns_tokens_for_valid_credentials(self):
        user = self.create_user("login-user", "login@example.com")
        self.assertIsNone(user.last_login)
        client = self.client

        response = client.post(
            "/login/",
            {"username": "login-user", "password": self.password},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertIn("refresh-token", response.data)
        self.assertEqual(response.data["user"]["username"], "login-user")
        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)

    def test_failed_login_does_not_update_last_login(self):
        user = self.create_user("failed-login-user", "failed-login@example.com")

        response = self.client.post(
            "/login/",
            {"username": "failed-login-user", "password": "wrong-password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        user.refresh_from_db()
        self.assertIsNone(user.last_login)

    def test_google_login_requires_credential_or_token(self):
        response = self.client.post("/authenticate/login", {}, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Error", response.data)

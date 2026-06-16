from django.contrib.admin.sites import AdminSite
from django.contrib.admin.utils import flatten_fieldsets
from django.test import TestCase

from apps.user.admin import UserAdmin, UserAdminPasswordForm
from apps.user.models.user import User


class UserAdminPasswordFormTests(TestCase):
    def test_reset_password_hashes_new_password(self):
        user = User.objects.create_user(
            username="admin-reset",
            email="admin-reset@example.com",
            password="OldPass123!",
        )
        form = UserAdminPasswordForm(
            data={
                "username": user.username,
                "email": user.email,
                "is_active": "on",
                "new_password": "NewPass123!",
                "confirm_password": "NewPass123!",
                "groups": [],
                "user_permissions": [],
            },
            instance=user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        user.refresh_from_db()

        self.assertTrue(user.check_password("NewPass123!"))
        self.assertFalse(user.check_password("OldPass123!"))
        self.assertNotEqual(user.password, "NewPass123!")

    def test_password_confirmation_is_required_to_match(self):
        user = User.objects.create_user(
            username="admin-mismatch",
            email="admin-mismatch@example.com",
            password="OldPass123!",
        )
        form = UserAdminPasswordForm(
            data={
                "username": user.username,
                "email": user.email,
                "is_active": "on",
                "new_password": "NewPass123!",
                "confirm_password": "OtherPass123!",
                "groups": [],
                "user_permissions": [],
            },
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Las contrasenas no coinciden.", form.non_field_errors())


class UserAdminTests(TestCase):
    def test_admin_does_not_expose_raw_password_field(self):
        user_admin = UserAdmin(User, AdminSite())
        fields = flatten_fieldsets(user_admin.fieldsets)

        self.assertNotIn("password", fields)
        self.assertIn("password_status", fields)
        self.assertIn("new_password", fields)
        self.assertIn("confirm_password", fields)

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.base.permissions import IsRouteCompanyGenerator
from apps.base.test_utils import BackendTestMixin
from apps.base.utils import gen_password
from apps.route.models import Route


class BaseUtilsTests(BackendTestMixin, TestCase):
    def test_gen_password_returns_12_alnum_chars(self):
        password = gen_password()

        self.assertEqual(len(password), 12)
        self.assertTrue(password.isalnum())


class BasePermissionsTests(BackendTestMixin, TestCase):
    def test_is_route_company_generator_requires_same_company(self):
        owner_user, owner_worker, company = self.create_owner_context("perm-owner")
        _, other_owner_worker, other_company = self.create_owner_context("perm-other")
        route = Route.objects.create(
            name="Ruta Permisos",
            company=company,
            worker=owner_worker,
            start_date=self.today(),
            week_start=0,
            week_end=6,
        )

        permission = IsRouteCompanyGenerator()
        request = APIRequestFactory().get("/routes/")
        request.user = other_owner_worker.user

        self.assertFalse(permission.has_object_permission(request, None, route))

        request.user = owner_user
        self.assertTrue(permission.has_object_permission(request, None, route))

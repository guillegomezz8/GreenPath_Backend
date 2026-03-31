from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.base.enums import CollectionRequestStatus, CollectionStatus, Role
from apps.base.test_utils import BackendTestMixin
from apps.collection.models import Collection, CollectionRequest
from apps.route.models import Route, RouteDay, RouteDayClient


class CollectionApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("collection")
        self.client_user, self.client_profile = self.create_client(self.company, "collection-client")
        self.owner_client = self.api_client_for(self.owner_user)
        self.client_api = self.api_client_for(self.client_user)
        self.route = Route.objects.create(
            name="Ruta Collection",
            company=self.company,
            worker=self.owner_worker,
            start_date=self.today(),
            week_start=0,
            week_end=6,
        )
        self.route_day = RouteDay.objects.create(route=self.route, date=self.today())
        self.route_day_client = RouteDayClient.objects.create(route_day=self.route_day, client=self.client_profile, order=1)

    def test_client_can_answer_own_collection_request(self):
        collection_request = CollectionRequest.objects.create(
            route_day_client=self.route_day_client,
            expires_at=timezone.now() + timedelta(hours=4),
            status=CollectionRequestStatus.PENDING,
        )

        response = self.client_api.post(
            f"/collections/requests/{collection_request.id}/answer/",
            {"final_liters": "75.50"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        collection_request.refresh_from_db()
        self.assertEqual(collection_request.status, CollectionRequestStatus.ANSWERED)
        self.assertEqual(collection_request.answered_by_id, self.client_user.id)
        self.assertEqual(collection_request.final_liters, Decimal("75.50"))

    def test_owner_can_filter_collections_by_billable(self):
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("70.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=False,
        )

        response = self.owner_client.get("/collections/?billable=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(response.data["results"][0]["billable"])

from datetime import timedelta

from django.test import TestCase

from apps.base.enums import CollectionRequestStatus, RouteDayStatus
from apps.base.test_utils import BackendTestMixin
from apps.collection.models import CollectionRequest
from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay


class RouteApiTests(BackendTestMixin, TestCase):
    def setUp(self):
        self.owner_user, self.owner_worker, self.company = self.create_owner_context("route")
        self.owner_client = self.api_client_for(self.owner_user)
        self.route = Route.objects.create(
            name="Ruta Operativa Test",
            company=self.company,
            worker=self.owner_worker,
            start_date=self.today(),
            week_start=0,
            week_end=6,
        )

    def test_generate_week_creates_route_day_stops_and_collection_requests(self):
        zone = self.create_zone("Zona Generacion")
        RouteZoneDay.objects.create(route=self.route, weekday=self.today().weekday()).zones.add(zone)
        _, client = self.create_client(
            self.company,
            "route-client",
            location=self.point_inside_default_polygon(),
        )

        response = self.owner_client.post(
            f"/routes/{self.route.id}/generate-week/",
            {
                "week_start_date": self.today().isoformat(),
                "daily_capacity_liters": "500.00",
                "auto_estimate_without_contact": True,
                "max_clients_per_day": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        route_day = RouteDay.objects.get(route=self.route, date=self.today())
        route_day_client = RouteDayClient.objects.get(route_day=route_day, client=client)
        collection_request = CollectionRequest.objects.get(route_day_client=route_day_client)

        self.assertEqual(route_day.daily_capacity_liters, 500)
        self.assertEqual(route_day.ordered_clients.count(), 1)
        self.assertEqual(collection_request.status, CollectionRequestStatus.AUTO_ESTIMATED)
        self.assertIsNotNone(collection_request.final_liters)

    def test_finish_route_day_requires_decision_when_pending_stops_exist(self):
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today() + timedelta(days=1),
            status=RouteDayStatus.IN_PROGRESS,
        )
        _, client = self.create_client(self.company, "pending-stop", location=self.point_inside_default_polygon())
        RouteDayClient.objects.create(route_day=route_day, client=client, order=1)

        response = self.owner_client.post(
            f"/routes/{self.route.id}/route-days/{route_day.id}/finish/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

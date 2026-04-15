from datetime import timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.utils import timezone

from apps.base.enums import CollectionRequestStatus, CollectionStatus, RouteDayStatus
from apps.base.test_utils import BackendTestMixin
from apps.collection.models import Collection
from apps.collection.models import CollectionRequest
from apps.company.models import CompanyHub
from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay
from apps.route.utils import build_route_day_operational_plan, get_route_day_google_navigation_url


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

    def test_generate_week_uses_same_company_history_for_planned_liters(self):
        zone = self.create_zone("Zona Scope Historia")
        RouteZoneDay.objects.create(route=self.route, weekday=self.today().weekday()).zones.add(zone)
        _, client = self.create_client(
            self.company,
            "shared-history-client",
            location=self.point_inside_default_polygon(),
        )

        other_owner_user, other_owner_worker, other_company = self.create_owner_context("route-other-company")
        client.companies.add(other_company)

        Collection.objects.create(
            client=client,
            worker=self.owner_worker,
            collection_date=self.today() - timedelta(days=8),
            container_number=1,
            measured_liters=Decimal("50.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CONFIRMED,
        )
        Collection.objects.create(
            client=client,
            worker=other_owner_worker,
            collection_date=self.today() - timedelta(days=9),
            container_number=7,
            measured_liters=Decimal("400.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CONFIRMED,
        )

        response = self.owner_client.post(
            f"/routes/{self.route.id}/generate-week/",
            {
                "week_start_date": self.today().isoformat(),
                "daily_capacity_liters": "100.00",
                "auto_estimate_without_contact": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        route_day = RouteDay.objects.get(route=self.route, date=self.today())
        self.assertEqual(route_day.ordered_clients.count(), 1)

    def test_generate_week_falls_back_to_estimated_liters_when_no_confirmed_history_exists(self):
        zone = self.create_zone("Zona Estimacion Fallback")
        RouteZoneDay.objects.create(route=self.route, weekday=self.today().weekday()).zones.add(zone)
        _, client = self.create_client(
            self.company,
            "estimated-history-client",
            location=self.point_inside_default_polygon(),
        )

        Collection.objects.create(
            client=client,
            worker=self.owner_worker,
            collection_date=self.today() - timedelta(days=8),
            container_number=3,
            measured_liters=None,
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.PENDING_MEASUREMENT,
        )

        response = self.owner_client.post(
            f"/routes/{self.route.id}/generate-week/",
            {
                "week_start_date": self.today().isoformat(),
                "daily_capacity_liters": "100.00",
                "auto_estimate_without_contact": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        route_day = RouteDay.objects.get(route=self.route, date=self.today())
        self.assertEqual(route_day.ordered_clients.count(), 0)

    def test_generate_week_uses_consistent_default_max_clients_per_day(self):
        zone = self.create_zone("Zona Max Clientes")
        RouteZoneDay.objects.create(route=self.route, weekday=self.today().weekday()).zones.add(zone)

        for index in range(20):
            self.create_client(
                self.company,
                f"max-client-{index}",
                location=self.point_inside_default_polygon(),
            )

        response = self.owner_client.post(
            f"/routes/{self.route.id}/generate-week/",
            {
                "week_start_date": self.today().isoformat(),
                "daily_capacity_liters": "2000.00",
                "auto_estimate_without_contact": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        route_day = RouteDay.objects.get(route=self.route, date=self.today())
        self.assertEqual(route_day.ordered_clients.count(), 10)

    def test_operational_plan_splits_segments_by_capacity_and_ignores_canceled_load(self):
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            status=RouteDayStatus.IN_PROGRESS,
            daily_capacity_liters=Decimal("100.00"),
        )
        _, client_one = self.create_client(self.company, "seg-client-1", location=self.point_inside_default_polygon())
        _, client_two = self.create_client(self.company, "seg-client-2", location=self.point_inside_default_polygon())
        _, client_three = self.create_client(self.company, "seg-client-3", location=self.point_inside_default_polygon())

        stop_one = RouteDayClient.objects.create(route_day=route_day, client=client_one, order=1)
        stop_two = RouteDayClient.objects.create(route_day=route_day, client=client_two, order=2)
        stop_three = RouteDayClient.objects.create(route_day=route_day, client=client_three, order=3)

        CollectionRequest.objects.create(route_day_client=stop_one, expires_at=timezone.now(), final_liters=Decimal("60.00"))
        CollectionRequest.objects.create(route_day_client=stop_two, expires_at=timezone.now(), final_liters=Decimal("60.00"))
        CollectionRequest.objects.create(route_day_client=stop_three, expires_at=timezone.now(), final_liters=Decimal("60.00"))

        Collection.objects.create(
            client=client_one,
            route_day_client=stop_one,
            worker=self.owner_worker,
            collection_date=route_day.date,
            container_number=1,
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CONFIRMED,
        )
        Collection.objects.create(
            client=client_two,
            route_day_client=stop_two,
            worker=self.owner_worker,
            collection_date=route_day.date,
            container_number=1,
            measured_liters=None,
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CANCELED,
        )

        operational_plan = build_route_day_operational_plan(route_day)

        self.assertEqual(operational_plan["segments_count"], 3)
        self.assertEqual(operational_plan["returns_to_hub_count"], 2)
        self.assertTrue(operational_plan["requires_hub_return"])
        self.assertEqual(operational_plan["active_segment_number"], 3)
        self.assertEqual(operational_plan["registered_load_liters"], Decimal("60.00"))
        self.assertEqual(operational_plan["segments"][0]["completed_stops"], 1)
        self.assertEqual(operational_plan["segments"][1]["canceled_stops"], 1)
        self.assertEqual(operational_plan["segments"][2]["pending_stops"], 1)

    def test_operational_overview_includes_operational_plan(self):
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            status=RouteDayStatus.PLANNED,
            daily_capacity_liters=Decimal("180.00"),
        )
        _, client = self.create_client(self.company, "overview-plan-client", location=self.point_inside_default_polygon())
        stop = RouteDayClient.objects.create(route_day=route_day, client=client, order=1)
        CollectionRequest.objects.create(route_day_client=stop, expires_at=timezone.now(), final_liters=Decimal("60.00"))

        response = self.owner_client.get(f"/routes/{self.route.id}/operational-overview/")

        self.assertEqual(response.status_code, 200)
        route_days = response.data.get("route_days") or []
        self.assertEqual(len(route_days), 1)
        plan = route_days[0].get("operational_plan") or {}
        self.assertEqual(plan.get("segments_count"), 1)
        self.assertEqual(Decimal(plan.get("planned_load_liters")), Decimal("60.00"))

    def test_google_navigation_url_includes_hub_return_between_segments(self):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave test",
            location=Point(-6.0300, 37.3600, srid=4326),
        )
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            status=RouteDayStatus.PLANNED,
            daily_capacity_liters=Decimal("100.00"),
        )
        _, client_one = self.create_client(self.company, "nav-client-1", location=Point(-6.0100, 37.3800, srid=4326))
        _, client_two = self.create_client(self.company, "nav-client-2", location=Point(-5.9900, 37.3900, srid=4326))
        _, client_three = self.create_client(self.company, "nav-client-3", location=Point(-5.9700, 37.4000, srid=4326))

        stop_one = RouteDayClient.objects.create(route_day=route_day, client=client_one, order=1)
        stop_two = RouteDayClient.objects.create(route_day=route_day, client=client_two, order=2)
        stop_three = RouteDayClient.objects.create(route_day=route_day, client=client_three, order=3)

        CollectionRequest.objects.create(route_day_client=stop_one, expires_at=timezone.now(), final_liters=Decimal("60.00"))
        CollectionRequest.objects.create(route_day_client=stop_two, expires_at=timezone.now(), final_liters=Decimal("60.00"))
        CollectionRequest.objects.create(route_day_client=stop_three, expires_at=timezone.now(), final_liters=Decimal("60.00"))

        navigation_url = get_route_day_google_navigation_url(route_day)
        query = parse_qs(urlparse(navigation_url).query)
        waypoints = query.get("waypoints", [""])[0]

        self.assertEqual(query.get("origin", [""])[0], "37.36,-6.03")
        self.assertEqual(query.get("destination", [""])[0], "37.36,-6.03")
        self.assertIn("37.36,-6.03|37.39,-5.99", waypoints)

    def test_google_navigation_url_without_capacity_split_returns_to_hub_at_end(self):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave unica",
            location=Point(-6.0300, 37.3600, srid=4326),
        )
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            status=RouteDayStatus.PLANNED,
            daily_capacity_liters=Decimal("1000.00"),
        )
        _, client_one = self.create_client(self.company, "single-nav-client-1", location=Point(-6.0100, 37.3800, srid=4326))
        _, client_two = self.create_client(self.company, "single-nav-client-2", location=Point(-5.9900, 37.3900, srid=4326))

        stop_one = RouteDayClient.objects.create(route_day=route_day, client=client_one, order=1)
        stop_two = RouteDayClient.objects.create(route_day=route_day, client=client_two, order=2)

        CollectionRequest.objects.create(route_day_client=stop_one, expires_at=timezone.now(), final_liters=Decimal("60.00"))
        CollectionRequest.objects.create(route_day_client=stop_two, expires_at=timezone.now(), final_liters=Decimal("60.00"))

        navigation_url = get_route_day_google_navigation_url(route_day)
        query = parse_qs(urlparse(navigation_url).query)

        self.assertEqual(query.get("origin", [""])[0], "37.36,-6.03")
        self.assertEqual(query.get("destination", [""])[0], "37.36,-6.03")
        self.assertEqual(query.get("waypoints", [""])[0], "37.38,-6.01|37.39,-5.99")

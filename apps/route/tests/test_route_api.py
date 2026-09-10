from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from django.contrib.gis.geos import Point
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.base.enums import CollectionRequestStatus, CollectionStatus, RouteDayStatus
from apps.base.literals import ROUTE_DAY_CLIENT_LOCATION_REQUIRED
from apps.base.tests.helpers import BackendTestMixin
from apps.collection.models import Collection
from apps.collection.models import CollectionRequest
from apps.company.models import CompanyHub
from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay
from apps.route.utils import (
    build_route_day_operational_plan,
    get_route_day_google_navigation_url,
    get_route_day_google_navigation_urls,
    optimize_route_day_with_google,
)


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

    def test_owner_can_create_route_and_response_includes_created_id(self):
        worker_user, worker = self.create_worker(self.company, username="route-worker")

        response = self.owner_client.post(
            "/routes/",
            {
                "name": "Ruta Nueva Front",
                "worker": worker.id,
                "start_date": self.today().isoformat(),
                "end_date": None,
                "week_start": 0,
                "week_end": 6,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data)
        created_route = Route.objects.get(id=response.data["id"])
        self.assertEqual(created_route.name, "Ruta Nueva Front")
        self.assertEqual(created_route.company_id, self.company.id)
        self.assertEqual(created_route.worker_id, worker.id)

    def test_zone_config_rejects_zones_from_another_company(self):
        _, _, other_company = self.create_owner_context("route-zone-other")
        other_zone = self.create_zone(other_company, "Zona Externa")

        response = self.owner_client.put(
            f"/routes/{self.route.id}/zone-config/",
            {
                "zone_days": [
                    {
                        "weekday": self.today().weekday(),
                        "zones": [other_zone.id],
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(RouteZoneDay.objects.filter(route=self.route).exists())

    def test_zone_config_accepts_zones_from_route_company(self):
        zone = self.create_zone(self.company, "Zona Interna")

        response = self.owner_client.put(
            f"/routes/{self.route.id}/zone-config/",
            {
                "zone_days": [
                    {
                        "weekday": self.today().weekday(),
                        "zones": [zone.id],
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        route_zone_day = RouteZoneDay.objects.get(route=self.route, weekday=self.today().weekday())
        self.assertEqual(list(route_zone_day.zones.values_list("id", flat=True)), [zone.id])

    def test_generate_week_creates_route_day_stops_and_collection_requests(self):
        zone = self.create_zone(self.company, "Zona Generacion")
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
        zone = self.create_zone(self.company, "Zona Scope Historia")
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
        zone = self.create_zone(self.company, "Zona Estimacion Fallback")
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
        zone = self.create_zone(self.company, "Zona Max Clientes")
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

    def test_generate_week_orders_clients_by_effective_reference_date(self):
        zone = self.create_zone(self.company, "Zona Fecha Referencia")
        RouteZoneDay.objects.create(route=self.route, weekday=self.today().weekday()).zones.add(zone)
        _, client_recent_plan = self.create_client(
            self.company,
            "client-recent-plan",
            location=Point(-6.0100, 37.4000, srid=4326),
        )
        _, client_older_reference = self.create_client(
            self.company,
            "client-older-reference",
            location=Point(-6.0200, 37.4000, srid=4326),
        )

        Collection.objects.create(
            client=client_recent_plan,
            worker=self.owner_worker,
            collection_date=self.today() - timedelta(days=30),
            container_number=1,
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CONFIRMED,
        )
        Collection.objects.create(
            client=client_older_reference,
            worker=self.owner_worker,
            collection_date=self.today() - timedelta(days=20),
            container_number=1,
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.200"),
            status=CollectionStatus.CONFIRMED,
        )
        previous_route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today() - timedelta(days=8),
            status=RouteDayStatus.PLANNED,
        )
        RouteDayClient.objects.create(route_day=previous_route_day, client=client_recent_plan, order=1)

        response = self.owner_client.post(
            f"/routes/{self.route.id}/generate-week/",
            {
                "week_start_date": self.today().isoformat(),
                "daily_capacity_liters": "1000.00",
                "auto_estimate_without_contact": False,
                "max_clients_per_day": 10,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        route_day = RouteDay.objects.get(route=self.route, date=self.today())
        ordered_names = list(route_day.ordered_clients.order_by("order").values_list("client__name", flat=True))
        self.assertEqual(ordered_names, [client_older_reference.name, client_recent_plan.name])

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("apps.route.utils.requests.get")
    def test_google_optimization_rejects_unlocated_stops(self, mock_get):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave optimizacion",
            location=Point(-6.0300, 37.3600, srid=4326),
        )
        route_day = RouteDay.objects.create(route=self.route, date=self.today(), daily_capacity_liters=Decimal("1000.00"))
        _, client_one = self.create_client(self.company, "opt-client-1", location=Point(-6.0100, 37.3800, srid=4326))
        _, client_without_location = self.create_client(self.company, "opt-client-no-location", location=None)
        _, client_two = self.create_client(self.company, "opt-client-2", location=Point(-5.9900, 37.3900, srid=4326))

        stop_one = RouteDayClient.objects.create(route_day=route_day, client=client_one, order=1)
        stop_without_location = RouteDayClient.objects.create(route_day=route_day, client=client_without_location, order=2)
        stop_two = RouteDayClient.objects.create(route_day=route_day, client=client_two, order=3)

        google_response = Mock()
        google_response.raise_for_status.return_value = None
        google_response.json.return_value = {"routes": [{"waypoint_order": [1, 0]}]}
        mock_get.return_value = google_response

        with self.assertRaisesMessage(
            ValueError,
            ROUTE_DAY_CLIENT_LOCATION_REQUIRED.format(clients=client_without_location.name),
        ):
            optimize_route_day_with_google(route_day)

        mock_get.assert_not_called()
        self.assertEqual(
            list(route_day.ordered_clients.order_by("order").values_list("id", flat=True)),
            [stop_one.id, stop_without_location.id, stop_two.id],
        )

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("apps.route.utils.requests.get")
    def test_google_optimization_groups_by_capacity_before_optimizing_segments(self, mock_get):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave segmentos",
            location=Point(-6.0300, 37.3600, srid=4326),
        )
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            daily_capacity_liters=Decimal("120.00"),
        )
        stops = []
        for index in range(4):
            _, client = self.create_client(
                self.company,
                f"segment-client-{index}",
                location=Point(-6.0100 + (index * 0.01), 37.3800 + (index * 0.01), srid=4326),
            )
            stop = RouteDayClient.objects.create(route_day=route_day, client=client, order=index + 1)
            CollectionRequest.objects.create(route_day_client=stop, expires_at=timezone.now(), final_liters=Decimal("60.00"))
            stops.append(stop)

        google_response = Mock()
        google_response.raise_for_status.return_value = None
        google_response.json.return_value = {"routes": [{"waypoint_order": [1, 0]}]}
        mock_get.return_value = google_response

        optimized = optimize_route_day_with_google(route_day)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual([row.id for row in optimized], [stops[1].id, stops[0].id, stops[3].id, stops[2].id])
        self.assertEqual(list(route_day.ordered_clients.order_by("order").values_list("id", flat=True)), [stops[1].id, stops[0].id, stops[3].id, stops[2].id])

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("apps.route.utils.requests.get")
    def test_google_optimization_builds_capacity_segments_by_proximity_to_hub(self, mock_get):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave segmentos cercanos",
            location=Point(-6.0000, 37.0000, srid=4326),
        )
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            daily_capacity_liters=Decimal("120.00"),
        )
        stop_specs = [
            ("far-one", Point(-6.4000, 37.4000, srid=4326)),
            ("near-one", Point(-6.0100, 37.0100, srid=4326)),
            ("near-two", Point(-6.0200, 37.0200, srid=4326)),
            ("far-two", Point(-6.4100, 37.4100, srid=4326)),
        ]
        stops = []
        for index, (name, location) in enumerate(stop_specs):
            _, client = self.create_client(self.company, name, location=location)
            stop = RouteDayClient.objects.create(route_day=route_day, client=client, order=index + 1)
            CollectionRequest.objects.create(route_day_client=stop, expires_at=timezone.now(), final_liters=Decimal("60.00"))
            stops.append(stop)

        google_response = Mock()
        google_response.raise_for_status.return_value = None
        google_response.json.return_value = {"routes": [{"waypoint_order": [0, 1]}]}
        mock_get.return_value = google_response

        optimized = optimize_route_day_with_google(route_day)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual([row.id for row in optimized], [stops[1].id, stops[2].id, stops[0].id, stops[3].id])
        self.assertEqual(
            list(route_day.ordered_clients.order_by("order").values_list("id", flat=True)),
            [stops[1].id, stops[2].id, stops[0].id, stops[3].id],
        )

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

    def test_google_navigation_urls_split_long_days_by_waypoint_limit(self):
        CompanyHub.objects.create(
            company=self.company,
            name="Nave con limite",
            location=Point(-6.0300, 37.3600, srid=4326),
        )
        route_day = RouteDay.objects.create(
            route=self.route,
            date=self.today(),
            status=RouteDayStatus.PLANNED,
            daily_capacity_liters=Decimal("1000.00"),
        )

        for index in range(10):
            _, client = self.create_client(
                self.company,
                f"nav-limit-client-{index}",
                location=Point(-6.0100 + (index * 0.001), 37.3800 + (index * 0.001), srid=4326),
            )
            stop = RouteDayClient.objects.create(route_day=route_day, client=client, order=index + 1)
            CollectionRequest.objects.create(route_day_client=stop, expires_at=timezone.now(), final_liters=Decimal("60.00"))

        navigation_urls = get_route_day_google_navigation_urls(route_day, max_waypoints=4)

        self.assertEqual(len(navigation_urls), 3)
        waypoint_lengths = []
        for navigation_url in navigation_urls:
            query = parse_qs(urlparse(navigation_url).query)
            self.assertEqual(query.get("origin", [""])[0], "37.36,-6.03")
            self.assertEqual(query.get("destination", [""])[0], "37.36,-6.03")
            waypoints = query.get("waypoints", [""])[0]
            waypoint_lengths.append(len(waypoints.split("|")) if waypoints else 0)
        self.assertEqual(waypoint_lengths, [4, 4, 2])

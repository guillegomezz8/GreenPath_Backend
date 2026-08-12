from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.base.enums import CollectionRequestStatus, CollectionStatus, ContainerType
from apps.base.tests.helpers import BackendTestMixin
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
            {"container_type": ContainerType.BIDONES, "container_number": 3},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        collection_request.refresh_from_db()
        self.assertEqual(collection_request.status, CollectionRequestStatus.ANSWERED)
        self.assertEqual(collection_request.answered_by_id, self.client_user.id)
        self.assertEqual(collection_request.container_type, ContainerType.BIDONES)
        self.assertEqual(collection_request.container_number, 3)
        self.assertEqual(collection_request.final_liters, Decimal("180.00"))
        self.assertEqual(collection_request.estimated_liters, Decimal("180.00"))

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

    def test_owner_can_filter_collections_by_date_range(self):
        Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=date(2026, 1, 12),
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )
        included_collection = Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=date(2026, 3, 15),
            measured_liters=Decimal("70.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )

        response = self.owner_client.get("/collections/?start_date=2026-03-01&end_date=2026-03-31")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], included_collection.id)

    def test_client_searches_collections_by_worker_or_date_without_notes(self):
        collection = Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=date(2026, 5, 11),
            measured_liters=Decimal("70.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
            notes="nota interna sensible",
        )

        worker_response = self.client_api.get("/collections/?search=Owner")
        date_response = self.client_api.get("/collections/?search=11/5/2026")
        notes_response = self.client_api.get("/collections/?search=nota interna sensible")

        self.assertEqual(worker_response.status_code, 200)
        self.assertEqual(worker_response.data["count"], 1)
        self.assertEqual(worker_response.data["results"][0]["id"], collection.id)
        self.assertEqual(date_response.status_code, 200)
        self.assertEqual(date_response.data["count"], 1)
        self.assertEqual(date_response.data["results"][0]["id"], collection.id)
        self.assertEqual(notes_response.status_code, 200)
        self.assertEqual(notes_response.data["count"], 0)

    def test_collection_detail_exposes_client_and_worker_ids(self):
        collection = Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )

        response = self.owner_client.get(f"/collections/{collection.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["client"], self.client_profile.id)
        self.assertEqual(response.data["worker"], self.owner_worker.id)

    def test_update_preserves_paid_total_and_respects_manual_status(self):
        collection = Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            container_type=ContainerType.BIDONES,
            container_number=1,
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )
        original_total = collection.total_price

        response = self.owner_client.put(
            f"/collections/{collection.id}/",
            {
                "client": self.client_profile.id,
                "worker": self.owner_worker.id,
                "route_day_client": None,
                "collection_date": self.today().isoformat(),
                "container_type": ContainerType.BIDONES,
                "container_number": 1,
                "measured_liters": "100.00",
                "deduction_liters": "0.00",
                "deduction_reason": "",
                "deduction_notes": "",
                "price_per_liter": "1.000",
                "billable": True,
                "status": CollectionStatus.PENDING_MEASUREMENT,
                "notes": "Ajuste manual de litros sin recalcular importe abonado.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        collection.refresh_from_db()
        self.assertEqual(collection.measured_liters, Decimal("100.00"))
        self.assertEqual(collection.status, CollectionStatus.PENDING_MEASUREMENT)
        self.assertEqual(collection.deduction_reason, "")
        self.assertEqual(collection.total_price, original_total)

    def test_update_requires_deduction_reason_when_deducting_liters(self):
        collection = Collection.objects.create(
            client=self.client_profile,
            worker=self.owner_worker,
            collection_date=self.today(),
            container_type=ContainerType.BIDONES,
            container_number=1,
            measured_liters=Decimal("60.00"),
            deduction_liters=Decimal("0.00"),
            price_per_liter=Decimal("1.00"),
            status=CollectionStatus.CONFIRMED,
            billable=True,
        )

        response = self.owner_client.put(
            f"/collections/{collection.id}/",
            {
                "client": self.client_profile.id,
                "worker": self.owner_worker.id,
                "route_day_client": None,
                "collection_date": self.today().isoformat(),
                "container_type": ContainerType.BIDONES,
                "container_number": 1,
                "measured_liters": "60.00",
                "deduction_liters": "5.00",
                "deduction_reason": "",
                "deduction_notes": "",
                "price_per_liter": "1.000",
                "billable": True,
                "status": CollectionStatus.CONFIRMED,
                "notes": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

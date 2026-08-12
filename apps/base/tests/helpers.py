from datetime import date
from decimal import Decimal

from django.contrib.gis.geos import Point, Polygon
from rest_framework.test import APIClient

from apps.base.enums import PickupFrequency, Role
from apps.company.models import Company, CompanySettings
from apps.sale.models import Buyer
from apps.truck.models import Truck
from apps.user.models.client import Client
from apps.user.models.user import User
from apps.user.models.worker import Worker
from apps.zone.models import Zone


class BackendTestMixin:
    password = "TestPass123!"

    def create_user(self, username, email=None, password=None, is_staff=False, is_superuser=False):
        email = email or f"{username}@example.com"
        password = password or self.password
        if is_superuser:
            return User.objects.create_superuser(username=username, email=email, password=password)
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = is_staff
        user.save(update_fields=["is_staff"])
        return user

    def create_company(self, name="GreenPath Demo", owner_user=None):
        company = Company.objects.create(
            name=name,
            address="Poligono Industrial 1",
            phone="955000000",
            email="empresa@example.com",
            cif=f"CIF-{name[:6]}",
        )
        if owner_user:
            company.owner = owner_user
            company.save(update_fields=["owner"])
        CompanySettings.objects.get_or_create(company=company)
        return company

    def create_owner_context(self, name_suffix="main"):
        owner_user = self.create_user(f"owner-{name_suffix}", f"owner-{name_suffix}@example.com")
        company = self.create_company(f"Empresa {name_suffix.title()}")
        owner_worker = Worker.objects.create(
            user=owner_user,
            company=company,
            role=Role.OWNER,
            name="Owner",
            surname=name_suffix.title(),
            address="Calle Owner 1",
            phone="600000001",
            dni=f"OWNER{name_suffix[:2].upper()}",
        )
        company.owner = owner_user
        company.save(update_fields=["owner"])
        return owner_user, owner_worker, company

    def create_worker(self, company, username="worker", role=Role.WORKER):
        user = self.create_user(username, f"{username}@example.com")
        worker = Worker.objects.create(
            user=user,
            company=company,
            role=role,
            name=username.title(),
            surname="Tester",
            address="Calle Worker 1",
            phone="600000002",
            dni=f"{username[:8].upper()}123",
        )
        return user, worker

    def create_client(self, company, username="client", frequency=PickupFrequency.WEEKLY, location=None):
        user = self.create_user(username, f"{username}@example.com")
        client = Client.objects.create(
            user=user,
            name=username.title(),
            phone="600000003",
            cif=f"CIF-{username[:6].upper()}",
            address="Calle Cliente 1",
            city="Sevilla",
            postal_code="41001",
            country="Espana",
            frequency=frequency,
            location=location,
        )
        client.companies.add(company)
        return user, client

    def create_buyer(self, company, fiscal_name="Comprador Demo", tax_id="B12345678"):
        return Buyer.objects.create(
            company=company,
            fiscal_name=fiscal_name,
            tax_id=tax_id,
            fiscal_address="Calle Factura 1",
            postal_code="41001",
            city="Sevilla",
            province="Sevilla",
            country="Espana",
            email="comprador@example.com",
            phone="600000004",
        )

    def create_truck(self, company, registration_number="0000-TEST", driver=None, capacity_liters=Decimal("18000.00")):
        return Truck.objects.create(
            registration_number=registration_number,
            brand="Iveco",
            model="Daily",
            year=2024,
            capacity_liters=capacity_liters,
            company=company,
            driver=driver,
        )

    def create_zone(self, company, name="Zona Demo", polygon=None):
        polygon = polygon or self.default_polygon()
        return Zone.objects.create(company=company, name=name, polygon=polygon)

    def default_polygon(self):
        return Polygon(
            (
                (-6.05, 37.35),
                (-5.95, 37.35),
                (-5.95, 37.45),
                (-6.05, 37.45),
                (-6.05, 37.35),
            ),
            srid=4326,
        )

    def point_inside_default_polygon(self):
        return Point(-6.00, 37.40, srid=4326)

    def point_outside_default_polygon(self):
        return Point(-5.50, 37.90, srid=4326)

    def api_client_for(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def today(self):
        return date.today()

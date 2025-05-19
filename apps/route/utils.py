from datetime import date
from geopy.distance import geodesic
from apps.user.models.client import ClientPickupSchedule
from apps.route.models import RouteDay, RouteDayClient
from apps.user.models.client import Client
from apps.base.enums import Weekday
from datetime import timedelta


def generate_weekly_routes_from_clients(route, client_ids):
    """
    A partir de una ruta y lista de clientes, agrupa por días de recogida
    y genera rutas diarias optimizadas automáticamente.
    """
    clients = Client.objects.filter(id__in=client_ids)

    # Obtener todos los horarios de recogida de estos clientes
    schedules = ClientPickupSchedule.objects.filter(
        client__in=clients
    ).select_related('client')

    if not schedules.exists():
        raise ValueError("Ningún cliente tiene horario de recogida asignado.")

    # Agrupar por día de la semana
    grouped_by_weekday = {}
    for s in schedules:
        grouped_by_weekday.setdefault(s.weekday, []).append(s.client)

    route_days_created = []

    for weekday, clients_for_day in grouped_by_weekday.items():
        if not clients_for_day:
            continue

        # Calcular la próxima fecha real para ese día de la semana
        start = route.start_date
        while start.weekday() != weekday:
            start += timedelta(days=1)

        # Verificar coordenadas
        for c in clients_for_day:
            if c.latitude is None or c.longitude is None:
                raise ValueError(f"El cliente '{c.name}' no tiene coordenadas.")

        origin = (clients_for_day[0].latitude, clients_for_day[0].longitude)
        ordered = sorted(
            clients_for_day,
            key=lambda c: geodesic(origin, (c.latitude, c.longitude)).km
        )

        # Crear o actualizar RouteDay para esa fecha
        route_day, _ = RouteDay.objects.get_or_create(
            route=route,
            date=start,
            defaults={'name': f'{route.name} - {Weekday(weekday).label}'}
        )
        route_day.ordered_clients.all().delete()

        for i, client in enumerate(ordered, start=1):
            RouteDayClient.objects.create(
                route_day=route_day,
                client=client,
                order=i
            )

        route_days_created.append(route_day)

    return route_days_created


def generate_manual_day_route(route, route_date, client_ids: list[int]):
    """
    Genera un RouteDay manual ignorando horarios, para una fecha y lista de clientes específica.
    """
    clients = Client.objects.filter(id__in=client_ids)

    for c in clients:
        if c.latitude is None or c.longitude is None:
            raise ValueError(f"El cliente {c.name} no tiene coordenadas.")

    origin = (clients[0].latitude, clients[0].longitude)
    ordered = sorted(clients, key=lambda c: geodesic(origin, (c.latitude, c.longitude)).km)

    route_day, _ = RouteDay.objects.get_or_create(
        route=route,
        date=route_date,
        defaults={'name': f"{route.name} - {route_date.strftime('%A %d/%m/%Y')}"}
    )

    route_day.ordered_clients.all().delete()

    for i, client in enumerate(ordered, start=1):
        RouteDayClient.objects.create(
            route_day=route_day,
            client=client,
            order=i
        )

    return route_day


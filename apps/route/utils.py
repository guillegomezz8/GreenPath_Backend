from datetime import timedelta
from django.conf import settings
import requests
import logging

from apps.user.models.client import Client
from apps.route.models import RouteDay, RouteDayClient, RouteZoneDay
from apps.zone.models import Zone
from apps.base.enums import PickupFrequency

logger = logging.getLogger(__name__)


def should_pickup_client(client, target_date):
    week_number = target_date.isocalendar()[1]

    if client.frequency == PickupFrequency.WEEKLY:
        return True
    elif client.frequency == PickupFrequency.TWO_WEEKS:
        return week_number % 2 == 0
    elif client.frequency == PickupFrequency.THREE_WEEKS:
        return week_number % 3 == 0
    elif client.frequency == PickupFrequency.FOUR_WEEKS:
        return week_number % 4 == 0

    return False


def get_clients_for_day(route, date):
    weekday = date.weekday()

    try:
        zone_day = RouteZoneDay.objects.get(route=route, weekday=weekday)
    except RouteZoneDay.DoesNotExist:
        logger.info(f"No zone config for weekday {weekday} in route {route.id}")
        return []

    zones = zone_day.zones.all()
    clients = Client.objects.filter(companies=route.company, location__isnull=False)

    active_clients = []
    for client in clients:
        if not should_pickup_client(client, date):
            continue
        if any(zone.polygon.contains(client.location) for zone in zones):
            active_clients.append(client)

    return active_clients


def get_optimized_order_from_google(clients):
    if len(clients) < 2:
        return clients

    api_key = settings.GOOGLE_MAPS_API_KEY
    waypoints = '|'.join(f"{c.location.y},{c.location.x}" for c in clients)
    origin = f"{clients[0].location.y},{clients[0].location.x}"
    destination = f"{clients[-1].location.y},{clients[-1].location.x}"

    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}&destination={destination}"
        f"&waypoints=optimize:true|{waypoints}"
        f"&key={api_key}"
    )

    response = requests.get(url)
    data = response.json()

    if 'routes' not in data or not data['routes']:
        logger.error(f"Google Maps API error: {data}")
        raise ValueError("Google Maps no devolvió una ruta válida")

    order = data['routes'][0]['waypoint_order']
    return [clients[i] for i in order]


def generate_routes_for_date_range(route, start_date, end_date, zone_schedule, max_clients=25):
    current_date = start_date
    route_days = []

    while current_date <= end_date:
        weekday = current_date.weekday()

        if weekday in zone_schedule:
            zone_names = zone_schedule[weekday]
            logger.info(f"Generando ruta para {current_date} (día {weekday}) con zonas: {zone_names}")

            zone_objs = Zone.objects.filter(name__in=zone_names)
            route_zone_day, _ = RouteZoneDay.objects.get_or_create(route=route, weekday=weekday)
            route_zone_day.zones.set(zone_objs)

            clients = get_clients_for_day(route, current_date)

            if not clients:
                current_date += timedelta(days=1)
                continue

            clients = clients[:max_clients]
            optimized_clients = get_optimized_order_from_google(clients)

            route_day, created = RouteDay.objects.get_or_create(
                route=route,
                date=current_date,
                defaults={"name": f"{route.name} - {current_date.strftime('%A %d/%m')}"}
            )

            if not created:
                route_day.ordered_clients.all().delete()

            for i, client in enumerate(optimized_clients, start=1):
                RouteDayClient.objects.create(
                    route_day=route_day,
                    client=client,
                    order=i
                )

            route_days.append(route_day)

        current_date += timedelta(days=1)

    return route_days

from datetime import timedelta, datetime, time
from functools import reduce
import logging

import requests
from celery import current_app
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, Max
from django.utils import timezone

from apps.base.enums import PickupFrequency, CollectionRequestStatus, CollectionStatus
from apps.base.literals import (
    ROUTE_GOOGLE_NO_VALID_ROUTE,
    ROUTE_WEEK_GENERATION_IN_PROGRESS,
    ROUTE_WEEK_OUTSIDE_ROUTE_RANGE,
)
from apps.collection.models import Collection, CollectionRequest
from apps.collection.tasks import auto_estimate_collection_request_liters, notify_collection_request_created
from apps.company.models import CompanyHub
from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay
from apps.user.models.client import Client
from apps.zone.models import Zone

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
        logger.info(f"[route_utils - get_clients_for_day] No hay configuracion de zonas para ruta {route.id} en weekday {weekday}")
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
    waypoints = "|".join(f"{c.location.y},{c.location.x}" for c in clients)
    origin = f"{clients[0].location.y},{clients[0].location.x}"
    destination = f"{clients[-1].location.y},{clients[-1].location.x}"

    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origin}&destination={destination}"
        f"&waypoints=optimize:true|{waypoints}"
        f"&key={api_key}"
    )

    response = requests.get(url, timeout=10)
    data = response.json()

    if "routes" not in data or not data["routes"]:
        logger.error(f"[route_utils - get_optimized_order_from_google] Google Maps API sin rutas validas: {data}")
        raise ValueError(ROUTE_GOOGLE_NO_VALID_ROUTE)

    order = data["routes"][0]["waypoint_order"]
    return [clients[i] for i in order]


def _frequency_days(frequency):
    if frequency == PickupFrequency.WEEKLY:
        return 7
    if frequency == PickupFrequency.TWO_WEEKS:
        return 14
    if frequency == PickupFrequency.THREE_WEEKS:
        return 21
    if frequency == PickupFrequency.FOUR_WEEKS:
        return 28
    return 7


def _is_client_due(client, target_date, last_collection_date=None):
    days = _frequency_days(client.frequency)

    if last_collection_date is None:
        last_collection = (
            Collection.objects
            .filter(client=client, collection_date__lt=target_date)
            .exclude(status=CollectionStatus.CANCELED)
            .order_by("-collection_date")
            .first()
        )
        last_collection_date = last_collection.collection_date if last_collection else None

    if not last_collection_date:
        return True

    return (target_date - last_collection_date).days >= days


def _route_day_start_datetime(route_day):
    naive = datetime.combine(route_day.date, time.min)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def _build_auto_estimate_task_id(collection_request_id, expires_at):
    return f"collection_request_auto_estimate_{collection_request_id}_{int(expires_at.timestamp())}"


def _revoke_collection_request_task(collection_request):
    task_id = collection_request.auto_estimate_task_id or _build_auto_estimate_task_id(collection_request.id, collection_request.expires_at)
    try:
        current_app.control.revoke(task_id, terminate=False)
        logger.info(f"[route_utils - _revoke_collection_request_task] Task {task_id} revocada para solicitud {collection_request.id}")
    except Exception as exc:
        logger.warning(f"[route_utils - _revoke_collection_request_task] No se pudo revocar task {task_id} para solicitud {collection_request.id}: {exc}")


def _enqueue_auto_estimate_task(collection_request, task_id):
    def _enqueue():
        if collection_request.expires_at <= timezone.now():
            auto_estimate_collection_request_liters.apply_async(args=[collection_request.id], task_id=task_id)
        else:
            auto_estimate_collection_request_liters.apply_async(args=[collection_request.id], eta=collection_request.expires_at, task_id=task_id)
        logger.info(f"[route_utils - _enqueue_auto_estimate_task] Task programada para solicitud {collection_request.id} con task_id {task_id}")

    transaction.on_commit(_enqueue)


def _enqueue_collection_request_notification(collection_request):
    transaction.on_commit(lambda: notify_collection_request_created.delay(collection_request.id))
    logger.info(f"[route_utils - _enqueue_collection_request_notification] Notificacion encolada para solicitud {collection_request.id}")


def _schedule_collection_request(route_day_client, route_day_start):
    expires_at = route_day_start - timedelta(hours=36)
    created = False

    with transaction.atomic():
        try:
            collection_request = CollectionRequest.objects.select_for_update().get(route_day_client=route_day_client)
        except CollectionRequest.DoesNotExist:
            try:
                collection_request = CollectionRequest.objects.create(route_day_client=route_day_client, expires_at=expires_at)
                created = True
            except IntegrityError:
                collection_request = CollectionRequest.objects.select_for_update().get(route_day_client=route_day_client)

        old_task_id = collection_request.auto_estimate_task_id
        updated_expiration = False
        if collection_request.expires_at != expires_at:
            collection_request.expires_at = expires_at
            updated_expiration = True

        if collection_request.status == CollectionRequestStatus.PENDING:
            task_id = _build_auto_estimate_task_id(collection_request.id, collection_request.expires_at)
            should_schedule = created or updated_expiration or old_task_id != task_id or (collection_request.expires_at <= timezone.now())

            if should_schedule:
                collection_request.auto_estimate_task_id = task_id
                collection_request.auto_estimate_scheduled_at = timezone.now()
                collection_request.save(update_fields=["expires_at", "auto_estimate_task_id", "auto_estimate_scheduled_at", "modified_date"])
                if old_task_id and old_task_id != task_id:
                    try:
                        current_app.control.revoke(old_task_id, terminate=False)
                        logger.info(f"[route_utils - _schedule_collection_request] Task anterior {old_task_id} revocada para solicitud {collection_request.id}")
                    except Exception as e:
                        logger.warning(f"[route_utils - _schedule_collection_request] No se pudo revocar task anterior {old_task_id} para solicitud {collection_request.id}: {str(e)}")
                _enqueue_auto_estimate_task(collection_request, task_id)
            elif updated_expiration:
                collection_request.save(update_fields=["expires_at", "modified_date"])
        elif updated_expiration:
            collection_request.save(update_fields=["expires_at", "modified_date"])

        if created:
            _enqueue_collection_request_notification(collection_request)


def _revoke_route_day_collection_request_tasks(route_day):
    requests_qs = CollectionRequest.objects.filter(route_day_client__route_day=route_day)
    for collection_request in requests_qs:
        _revoke_collection_request_task(collection_request)


def optimize_route_day_with_google(route_day):
    route_day_clients = list(route_day.ordered_clients.select_related("client").order_by("order"))
    if len(route_day_clients) < 2:
        return route_day_clients

    hub = CompanyHub.objects.filter(company=route_day.route.company, location__isnull=False).first()
    if not hub:
        logger.info(f"[route_utils - optimize_route_day_with_google] No hay hub para company {route_day.route.company_id}, se mantiene orden actual")
        return route_day_clients

    api_key = settings.GOOGLE_MAPS_API_KEY if hasattr(settings, "GOOGLE_MAPS_API_KEY") else ""
    if not api_key:
        logger.warning("[route_utils - optimize_route_day_with_google] GOOGLE_MAPS_API_KEY no configurada, se mantiene orden actual")
        return route_day_clients

    destination_row = max(route_day_clients, key=lambda row: row.client.location.distance(hub.location))
    waypoints_rows = [row for row in route_day_clients if row.id != destination_row.id]

    origin = f"{hub.location.y},{hub.location.x}"
    destination = f"{destination_row.client.location.y},{destination_row.client.location.x}"
    waypoints = "|".join(f"{row.client.location.y},{row.client.location.x}" for row in waypoints_rows)

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "waypoints": f"optimize:true|{waypoints}" if waypoints else "",
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.error(f"[route_utils - optimize_route_day_with_google] Error consultando Google Directions API: {exc}")
        return route_day_clients

    routes = data.get("routes") or []
    if not routes:
        logger.warning(f"[route_utils - optimize_route_day_with_google] Google Directions sin rutas validas: {data}")
        return route_day_clients

    waypoint_order = routes[0].get("waypoint_order", [])
    optimized = [waypoints_rows[index] for index in waypoint_order if index < len(waypoints_rows)]
    optimized.append(destination_row)

    for order, row in enumerate(optimized, start=1):
        if row.order != order:
            row.order = order
            row.save(update_fields=["order"])

    return optimized


def generate_route_day_clients(route_day, regenerate=False, reserved_client_ids=None):
    try:
        reserved_client_ids = reserved_client_ids or set()

        zone_day = (
            RouteZoneDay.objects
            .filter(route=route_day.route, weekday=route_day.weekday)
            .prefetch_related("zones")
            .first()
        )

        if regenerate:
            _revoke_route_day_collection_request_tasks(route_day)
            route_day.ordered_clients.all().delete()
        elif reserved_client_ids:
            duplicate_rows = list(route_day.ordered_clients.filter(client_id__in=reserved_client_ids))
            if duplicate_rows:
                for row in duplicate_rows:
                    collection_request = CollectionRequest.objects.filter(route_day_client=row).first()
                    if collection_request:
                        _revoke_collection_request_task(collection_request)
                duplicate_row_ids = [row.id for row in duplicate_rows]
                route_day.ordered_clients.filter(id__in=duplicate_row_ids).delete()
                logger.warning(f"[route_utils - generate_route_day_clients] Eliminadas {len(duplicate_row_ids)} paradas duplicadas en route_day {route_day.id}")

        if not zone_day:
            return []

        zones = list(zone_day.zones.all())
        if not zones:
            return []

        zone_filters = [Q(location__within=zone.polygon) for zone in zones if zone.polygon]
        if not zone_filters:
            return []

        spatial_q = reduce(lambda acc, item: acc | item, zone_filters)
        clients_qs = (
            Client.objects
            .filter(companies=route_day.route.company, location__isnull=False)
            .filter(spatial_q)
            .annotate(
                last_collection_date=Max(
                    "collections__collection_date",
                    filter=Q(collections__collection_date__lt=route_day.date) & ~Q(collections__status=CollectionStatus.CANCELED),
                )
            )
            .distinct()
        )

        due_clients = [client for client in clients_qs if _is_client_due(client, route_day.date, last_collection_date=client.last_collection_date)]
        existing_client_ids = set(route_day.ordered_clients.values_list("client_id", flat=True))
        next_order = int(route_day.ordered_clients.aggregate(max_order=Max("order"))["max_order"] or 0) + 1

        for client in due_clients:
            if client.id in existing_client_ids or client.id in reserved_client_ids:
                continue
            RouteDayClient.objects.create(route_day=route_day, client=client, order=next_order)
            next_order += 1

        optimized_rows = optimize_route_day_with_google(route_day)
        route_day_start = _route_day_start_datetime(route_day)

        for row in optimized_rows:
            _schedule_collection_request(row, route_day_start)

        return optimized_rows
    except Exception as e:
        logger.error(f"[route_utils - generate_route_day_clients] Error generando paradas para route_day {route_day.id}: {str(e)}")
        raise


def _is_weekday_enabled(route, weekday):
    if route.week_start <= route.week_end:
        return route.week_start <= weekday <= route.week_end
    return weekday >= route.week_start or weekday <= route.week_end


def _is_route_date_in_range(route, target_date):
    if target_date < route.start_date:
        return False
    if route.end_date and target_date > route.end_date:
        return False
    return True


@transaction.atomic
def generate_week_for_route(route, week_start_date, regenerate=False, daily_capacity_liters=None, days=None):
    lock_key = f"route_week_generation_lock_{route.id}_{week_start_date.isoformat()}"
    if not cache.add(lock_key, "1", timeout=300):
        logger.warning(f"[route_utils - generate_week_for_route] Lock activo para ruta {route.id} y semana {week_start_date}")
        raise ValueError(ROUTE_WEEK_GENERATION_IN_PROGRESS)

    try:
        locked_route = Route.objects.select_for_update().get(id=route.id)
        week_end_date = week_start_date + timedelta(days=6)
        if week_end_date < locked_route.start_date or (locked_route.end_date and week_start_date > locked_route.end_date):
            logger.warning(f"[route_utils - generate_week_for_route] Semana {week_start_date} fuera de rango para ruta {locked_route.id}")
            raise ValueError(ROUTE_WEEK_OUTSIDE_ROUTE_RANGE)

        days = days or []
        capacities_by_date = {item["date"]: item["daily_capacity_liters"] for item in days}
        week_assigned_client_ids = set()

        route_days = []
        for i in range(7):
            target_date = week_start_date + timedelta(days=i)
            weekday = target_date.weekday()

            if not _is_route_date_in_range(locked_route, target_date):
                continue

            if not _is_weekday_enabled(locked_route, weekday):
                continue

            route_day, _ = RouteDay.objects.get_or_create(route=locked_route, date=target_date)

            if daily_capacity_liters is not None:
                route_day.daily_capacity_liters = daily_capacity_liters
                route_day.save(update_fields=["daily_capacity_liters"])
            elif target_date in capacities_by_date:
                route_day.daily_capacity_liters = capacities_by_date[target_date]
                route_day.save(update_fields=["daily_capacity_liters"])

            generate_route_day_clients(route_day, regenerate=regenerate, reserved_client_ids=week_assigned_client_ids)
            week_assigned_client_ids.update(route_day.ordered_clients.values_list("client_id", flat=True))
            route_days.append(route_day)

        logger.info(f"[route_utils - generate_week_for_route] Semana generada para ruta {locked_route.id} con {len(route_days)} route_days")
        return route_days
    except Exception as e:
        logger.error(f"[route_utils - generate_week_for_route] Error generando semana para ruta {route.id}: {str(e)}")
        raise
    finally:
        cache.delete(lock_key)


def generate_routes_for_date_range(route, start_date, end_date, zone_schedule, max_clients=25):
    try:
        current_date = start_date
        route_days = []

        while current_date <= end_date:
            weekday = current_date.weekday()

            if weekday in zone_schedule:
                zone_names = zone_schedule[weekday]
                logger.info(f"[route_utils - generate_routes_for_date_range] Generando ruta para {current_date} (dia {weekday}) con zonas {zone_names}")

                zone_objs = Zone.objects.filter(name__in=zone_names)
                route_zone_day, _ = RouteZoneDay.objects.get_or_create(route=route, weekday=weekday)
                route_zone_day.zones.set(zone_objs)

                clients = get_clients_for_day(route, current_date)

                if not clients:
                    current_date += timedelta(days=1)
                    continue

                clients = clients[:max_clients]
                optimized_clients = get_optimized_order_from_google(clients)

                route_day, created = RouteDay.objects.get_or_create(route=route, date=current_date)

                if not created:
                    route_day.ordered_clients.all().delete()

                for i, client in enumerate(optimized_clients, start=1):
                    RouteDayClient.objects.create(route_day=route_day, client=client, order=i)

                route_days.append(route_day)

            current_date += timedelta(days=1)

        return route_days
    except Exception as e:
        logger.error(f"[route_utils - generate_routes_for_date_range] Error generando rutas para rango {start_date} - {end_date}: {str(e)}")
        raise

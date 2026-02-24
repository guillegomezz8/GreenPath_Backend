from datetime import timedelta, datetime, time
from decimal import Decimal
from functools import reduce
import logging
from urllib.parse import urlencode

import requests
from celery import current_app
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, Max, Avg
from django.utils import timezone

from apps.base.enums import PickupFrequency, CollectionRequestStatus, CollectionStatus, RouteDayStatus, PlannedSource, ContainerType
from apps.base.literals import (
    ROUTE_GOOGLE_NO_VALID_ROUTE,
    ROUTE_WEEK_GENERATION_IN_PROGRESS,
    ROUTE_WEEK_OUTSIDE_ROUTE_RANGE,
    ROUTE_DAY_START_INVALID_STATUS,
    ROUTE_DAY_FINISH_INVALID_STATUS,
    ROUTE_DAY_STOP_ROUTE_NOT_STARTED,
    ROUTE_DAY_STOP_ALREADY_COMPLETED,
    ROUTE_DAY_STOP_OUT_OF_ORDER,
    ROUTE_DAY_GOOGLE_NAVIGATION_EMPTY,
    ROUTE_DAY_GOOGLE_HUB_REQUIRED,
    ROUTE_DAY_FINISH_DECISION_REQUIRED,
    ROUTE_DAY_FINISH_CLOSE_ACTION_INVALID,
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


def _compute_auto_estimated_liters(collection_request):
    client_id = collection_request.route_day_client.client_id
    historical_avg = (
        Collection.objects
        .filter(client_id=client_id)
        .exclude(status=CollectionStatus.CANCELED)
        .aggregate(avg_liters=Avg("net_liters"))
        .get("avg_liters")
    )

    if historical_avg is not None:
        return Decimal(historical_avg).quantize(Decimal("0.01"))
    if collection_request.container_number:
        computed = collection_request.compute_client_liters()
        if computed is not None:
            return Decimal(computed).quantize(Decimal("0.01"))
    return Decimal("60.00")


def _apply_auto_estimate_without_contact(collection_request):
    estimated = _compute_auto_estimated_liters(collection_request)
    collection_request.estimated_liters = estimated

    if collection_request.final_liters is None or collection_request.status == CollectionRequestStatus.AUTO_ESTIMATED:
        collection_request.final_liters = estimated

    if not collection_request.final_source or collection_request.final_source == PlannedSource.AUTO:
        collection_request.final_source = PlannedSource.AUTO

    collection_request.status = CollectionRequestStatus.AUTO_ESTIMATED
    collection_request.auto_estimate_task_id = None
    collection_request.auto_estimate_scheduled_at = timezone.now()
    collection_request.save(
        update_fields=[
            "estimated_liters",
            "final_liters",
            "final_source",
            "status",
            "auto_estimate_task_id",
            "auto_estimate_scheduled_at",
            "modified_date",
        ]
    )
    logger.info(f"[route_utils - _apply_auto_estimate_without_contact] Solicitud {collection_request.id} autoestimada sin contacto con {estimated} litros")


def _schedule_collection_request(route_day_client, route_day_start, auto_estimate_without_contact=False):
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

        if auto_estimate_without_contact:
            if old_task_id:
                try:
                    current_app.control.revoke(old_task_id, terminate=False)
                    logger.info(f"[route_utils - _schedule_collection_request] Task anterior {old_task_id} revocada para solicitud {collection_request.id}")
                except Exception as e:
                    logger.warning(f"[route_utils - _schedule_collection_request] No se pudo revocar task anterior {old_task_id} para solicitud {collection_request.id}: {str(e)}")

            if updated_expiration:
                collection_request.save(update_fields=["expires_at", "modified_date"])

            if collection_request.status in [CollectionRequestStatus.ANSWERED, CollectionRequestStatus.MANUAL]:
                logger.info(f"[route_utils - _schedule_collection_request] Solicitud {collection_request.id} conservada en estado {collection_request.status} sin notificacion")
                return

            _apply_auto_estimate_without_contact(collection_request)
            return

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


def generate_route_day_clients(route_day, regenerate=False, reserved_client_ids=None, auto_estimate_without_contact=False):
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
            _schedule_collection_request(row, route_day_start, auto_estimate_without_contact=auto_estimate_without_contact)

        if route_day.status == RouteDayStatus.CANCELED and route_day.ordered_clients.exists():
            route_day.status = RouteDayStatus.PLANNED
            route_day.started_at = None
            route_day.finished_at = None
            route_day.save(update_fields=["status", "started_at", "finished_at"])

        return optimized_rows
    except Exception as e:
        logger.error(f"[route_utils - generate_route_day_clients] Error generando paradas para route_day {route_day.id}: {str(e)}")
        raise


@transaction.atomic
def start_route_day(route_day):
    if route_day.status not in [RouteDayStatus.PLANNED, RouteDayStatus.PARTIAL]:
        raise ValueError(ROUTE_DAY_START_INVALID_STATUS)

    now = timezone.now()
    route_day.status = RouteDayStatus.IN_PROGRESS
    if not route_day.started_at:
        route_day.started_at = now
    route_day.finished_at = None
    route_day.save(update_fields=["status", "started_at", "finished_at"])

    return route_day


@transaction.atomic
def finish_route_day(route_day, close_action=None):
    if route_day.status != RouteDayStatus.IN_PROGRESS:
        raise ValueError(ROUTE_DAY_FINISH_INVALID_STATUS)

    total_stops = route_day.ordered_clients.count()
    completed_stops = RouteDayClient.objects.filter(route_day=route_day, collections__isnull=False).distinct().count()
    canceled_stops = RouteDayClient.objects.filter(route_day=route_day, collections__status=CollectionStatus.CANCELED).distinct().count()

    normalized_action = close_action or None
    if normalized_action and normalized_action not in [RouteDayStatus.PARTIAL, RouteDayStatus.CANCELED]:
        raise ValueError(ROUTE_DAY_FINISH_CLOSE_ACTION_INVALID)

    pending_stops = max(total_stops - completed_stops, 0)

    if total_stops == 0:
        route_day.status = RouteDayStatus.CANCELED if not normalized_action else normalized_action
    elif pending_stops > 0:
        if not normalized_action:
            raise ValueError(ROUTE_DAY_FINISH_DECISION_REQUIRED)
        route_day.status = normalized_action
    elif canceled_stops > 0:
        route_day.status = RouteDayStatus.PARTIAL
    else:
        route_day.status = RouteDayStatus.COMPLETED

    now = timezone.now()
    if not route_day.started_at:
        route_day.started_at = now
    route_day.finished_at = now
    route_day.save(update_fields=["status", "started_at", "finished_at"])

    return route_day


def _resolve_worker_for_route_day(route_day, user, worker_id=None):
    if user.role_type == "worker" and hasattr(user, "worker_profile"):
        return user.worker_profile

    if worker_id:
        worker = route_day.route.workers.filter(id=worker_id).first()
        if worker and worker.company_id == route_day.route.company_id:
            return worker

    return route_day.route.workers.filter(company_id=route_day.route.company_id).order_by("id").first()


@transaction.atomic
def complete_route_day_client(route_day, route_day_client, user, payload):
    if route_day.status != RouteDayStatus.IN_PROGRESS:
        raise ValueError(ROUTE_DAY_STOP_ROUTE_NOT_STARTED)

    active_collection = Collection.objects.filter(route_day_client=route_day_client).exclude(status=CollectionStatus.CANCELED).first()
    if active_collection:
        raise ValueError(ROUTE_DAY_STOP_ALREADY_COMPLETED)

    force = payload.get("force", False)
    if not force:
        previous_pending_exists = (
            RouteDayClient.objects
            .filter(route_day=route_day, order__lt=route_day_client.order)
            .filter(collections__isnull=True)
            .exists()
        )
        if previous_pending_exists:
            raise ValueError(ROUTE_DAY_STOP_OUT_OF_ORDER)

    collection_request = CollectionRequest.objects.filter(route_day_client=route_day_client).first()
    worker = _resolve_worker_for_route_day(route_day, user, worker_id=payload.get("worker_id"))
    mark_as_canceled = payload.get("mark_as_canceled", False)

    notes = payload.get("notes") or ""

    container_type = payload.get("container_type") or ContainerType.BIDONES
    container_number = payload.get("container_number") or 1
    if collection_request:
        if "container_type" not in payload:
            container_type = collection_request.container_type or ContainerType.BIDONES
        if "container_number" not in payload:
            container_number = collection_request.container_number or 1

    measured_liters = None
    deduction_liters = Decimal("0.00")
    price_per_liter = Decimal("0.00")
    status_value = CollectionStatus.CANCELED if mark_as_canceled else CollectionStatus.PENDING_MEASUREMENT

    collection = Collection.objects.create(
        client=route_day_client.client,
        route_day_client=route_day_client,
        worker=worker,
        collection_date=route_day.date,
        container_type=container_type,
        container_number=container_number,
        measured_liters=measured_liters,
        deduction_liters=deduction_liters,
        price_per_liter=price_per_liter,
        status=status_value,
        notes=notes,
    )

    if collection_request:
        collection_request.container_type = container_type
        collection_request.container_number = container_number
        collection_request.final_source = PlannedSource.MANUAL
        collection_request.status = CollectionRequestStatus.MANUAL
        collection_request.manual_by = user
        collection_request.manual_at = timezone.now()
        if mark_as_canceled:
            collection_request.final_liters = Decimal("0.00")
            if collection_request.estimated_liters is None:
                collection_request.estimated_liters = Decimal("0.00")
        elif measured_liters is not None:
            collection_request.final_liters = measured_liters
            if collection_request.estimated_liters is None:
                collection_request.estimated_liters = measured_liters
        collection_request.save(update_fields=["container_type", "container_number", "final_source", "status", "manual_by", "manual_at", "final_liters", "estimated_liters", "modified_date"])

    return collection


def _planned_stop_liters(row):
    if hasattr(row, "collection_request") and row.collection_request:
        request_obj = row.collection_request
        if request_obj.final_liters is not None:
            return Decimal(request_obj.final_liters)
        if request_obj.estimated_liters is not None:
            return Decimal(request_obj.estimated_liters)
        computed = request_obj.compute_client_liters()
        if computed is not None:
            return Decimal(computed)
    return Decimal("0.00")


def get_route_day_google_navigation_url(route_day):
    route_day_clients = list(
        route_day.ordered_clients
        .select_related("client", "collection_request")
        .filter(client__location__isnull=False)
        .order_by("order")
    )
    if not route_day_clients:
        raise ValueError(ROUTE_DAY_GOOGLE_NAVIGATION_EMPTY)

    hub = CompanyHub.objects.filter(company=route_day.route.company, location__isnull=False).first()
    if not hub:
        raise ValueError(ROUTE_DAY_GOOGLE_HUB_REQUIRED)

    origin = f"{hub.location.y},{hub.location.x}"
    destination = origin

    capacity_limit = Decimal(route_day.daily_capacity_liters or 0)
    current_load = Decimal("0.00")
    waypoint_points = []

    for row in route_day_clients:
        stop_liters = _planned_stop_liters(row)
        if capacity_limit > 0 and current_load > 0 and current_load + stop_liters > capacity_limit:
            waypoint_points.append(origin)
            current_load = Decimal("0.00")

        waypoint_points.append(f"{row.client.location.y},{row.client.location.x}")
        current_load += stop_liters

    waypoints = "|".join(waypoint_points)

    params = {
        "api": "1",
        "origin": origin,
        "destination": destination,
        "travelmode": "driving",
    }
    if waypoints:
        params["waypoints"] = waypoints

    return f"https://www.google.com/maps/dir/?{urlencode(params, safe='|,')}"


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


def get_operational_week_start(route, reference_date):
    delta_days = (reference_date.weekday() - route.week_start) % 7
    return reference_date - timedelta(days=delta_days)


@transaction.atomic
def ensure_route_day_for_date(route, target_date):
    try:
        locked_route = Route.objects.select_for_update().get(id=route.id)
        if not _is_route_date_in_range(locked_route, target_date):
            return None
        if not _is_weekday_enabled(locked_route, target_date.weekday()):
            return None

        route_day, created = RouteDay.objects.get_or_create(route=locked_route, date=target_date)

        if created or not route_day.ordered_clients.exists():
            generate_route_day_clients(route_day, regenerate=False)
            logger.info(f"[route_utils - ensure_route_day_for_date] RouteDay {route_day.id} asegurado para fecha {target_date}")

        return route_day
    except Exception as e:
        logger.error(f"[route_utils - ensure_route_day_for_date] Error asegurando route_day para ruta {route.id} y fecha {target_date}: {str(e)}")
        raise


@transaction.atomic
def generate_week_for_route(route, week_start_date, regenerate=False, daily_capacity_liters=None, days=None, auto_estimate_without_contact=False):
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

            generate_route_day_clients(route_day, regenerate=regenerate, auto_estimate_without_contact=auto_estimate_without_contact)
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

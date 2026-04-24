from datetime import timedelta, datetime, time
from decimal import Decimal
from functools import reduce
import logging
import os
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
    ROUTE_WEEK_GENERATION_IN_PROGRESS,
    ROUTE_WEEK_OUTSIDE_ROUTE_RANGE,
    ROUTE_WEEK_REGENERATION_LOCKED,
    ROUTE_DAY_START_INVALID_STATUS,
    ROUTE_DAY_FINISH_INVALID_STATUS,
    ROUTE_DAY_STOP_ROUTE_NOT_STARTED,
    ROUTE_DAY_STOP_ALREADY_COMPLETED,
    ROUTE_DAY_STOP_OUT_OF_ORDER,
    ROUTE_DAY_GOOGLE_NAVIGATION_EMPTY,
    ROUTE_DAY_GOOGLE_HUB_REQUIRED,
    ROUTE_DAY_FINISH_DECISION_REQUIRED,
    ROUTE_DAY_FINISH_CLOSE_ACTION_INVALID,
    ROUTE_DAY_GENERATION_LOCKED,
    MAX_CLIENTS_PER_DAY
)
from apps.collection.models import Collection, CollectionRequest
from apps.collection.tasks import auto_estimate_collection_request_liters, notify_collection_request_created
from apps.company.models import CompanyHub
from apps.company.utils import resolve_default_collection_price_per_liter
from apps.route.models import Route, RouteDay, RouteDayClient, RouteZoneDay
from apps.user.models.client import Client
from apps.base.logger import configure_logging

configure_logging()

GOOGLE_MAPS_NAVIGATION_MAX_WAYPOINTS = 8


def _gmail_ready_for_notifications():
    gmail_from = os.environ.get("GMAIL_FROM")
    gmail_token_json = os.environ.get("GMAIL_TOKEN_JSON")
    gmail_client_secret_json = os.environ.get("GMAIL_CLIENT_SECRET_JSON")

    if not gmail_from:
        return False
    if not gmail_token_json:
        return False
    if not gmail_client_secret_json:
        return False
    return True


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


def _is_client_due(client, target_date, last_collection_date=None, last_planned_date=None):
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

    reference_date = last_collection_date
    if last_planned_date and (not reference_date or last_planned_date > reference_date):
        reference_date = last_planned_date

    if not reference_date:
        return True

    return (target_date - reference_date).days >= days


def _route_day_start_datetime(route_day):
    naive = datetime.combine(route_day.date, time.min)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def _build_auto_estimate_task_id(collection_request_id, expires_at):
    return f"collection_request_auto_estimate_{collection_request_id}_{int(expires_at.timestamp())}"


def _revoke_collection_request_task(collection_request):
    task_id = collection_request.auto_estimate_task_id or _build_auto_estimate_task_id(collection_request.id, collection_request.expires_at)
    try:
        current_app.control.revoke(task_id, terminate=False)
        logging.info(f"[route_utils - _revoke_collection_request_task] Task {task_id} revocada para solicitud {collection_request.id}")
    except Exception as exc:
        logging.warning(f"[route_utils - _revoke_collection_request_task] No se pudo revocar task {task_id} para solicitud {collection_request.id}: {exc}")


def _enqueue_auto_estimate_task(collection_request, task_id):
    def _enqueue():
        if collection_request.expires_at <= timezone.now():
            auto_estimate_collection_request_liters.apply_async(args=[collection_request.id], task_id=task_id)
        else:
            auto_estimate_collection_request_liters.apply_async(args=[collection_request.id], eta=collection_request.expires_at, task_id=task_id)
        logging.info(f"[route_utils - _enqueue_auto_estimate_task] Task programada para solicitud {collection_request.id} con task_id {task_id}")

    transaction.on_commit(_enqueue)


def _enqueue_collection_request_notification(collection_request):
    if not _gmail_ready_for_notifications():
        logging.info(f"[route_utils - _enqueue_collection_request_notification] Notificacion omitida por Gmail API no configurada para solicitud {collection_request.id}")
        return

    if collection_request.expires_at <= timezone.now():
        logging.info(f"[route_utils - _enqueue_collection_request_notification] Notificacion omitida para solicitud {collection_request.id}: ya expirada")
        return

    notify_lock_key = f"collection_request_notify_lock_{collection_request.id}"
    if not cache.add(notify_lock_key, "1", timeout=3600):
        logging.info(f"[route_utils - _enqueue_collection_request_notification] Notificacion ya encolada recientemente para solicitud {collection_request.id}")
        return

    transaction.on_commit(lambda: notify_collection_request_created.delay(collection_request.id))
    logging.info(f"[route_utils - _enqueue_collection_request_notification] Notificacion encolada para solicitud {collection_request.id}")


def _compute_auto_estimated_liters(collection_request):
    client_id = collection_request.route_day_client.client_id
    company = collection_request.route_day_client.route_day.route.company
    historical_avg = (
        _company_collection_history_queryset(company, client_ids=[client_id], statuses=[CollectionStatus.CONFIRMED])
        .aggregate(avg_liters=Avg("net_liters"))
        .get("avg_liters")
    )

    if historical_avg is not None:
        return Decimal(historical_avg).quantize(Decimal("0.01"))

    estimated_avg = (
        _company_collection_history_queryset(company, client_ids=[client_id])
        .aggregate(avg_estimated_liters=Avg("estimated_liters"))
        .get("avg_estimated_liters")
    )
    if estimated_avg is not None:
        return Decimal(estimated_avg).quantize(Decimal("0.01"))

    if collection_request.container_number:
        computed = collection_request.compute_client_liters()
        if computed is not None:
            return Decimal(computed).quantize(Decimal("0.01"))
    return Decimal("60.00")


def _company_collection_history_queryset(company, client_ids=None, statuses=None):
    queryset = Collection.objects.filter(_collection_scope_for_company(company)).distinct()
    if client_ids is not None:
        queryset = queryset.filter(client_id__in=client_ids)
    if statuses is not None:
        queryset = queryset.filter(status__in=statuses)
    else:
        queryset = queryset.exclude(status=CollectionStatus.CANCELED)
    return queryset


def _planned_liters_by_client_for_company(company, client_ids):
    confirmed_rows = (
        _company_collection_history_queryset(company, client_ids=client_ids, statuses=[CollectionStatus.CONFIRMED])
        .values("client_id")
        .annotate(avg_liters=Avg("net_liters"))
    )
    confirmed_avg_by_client = {item["client_id"]: item["avg_liters"] for item in confirmed_rows}

    estimated_rows = (
        _company_collection_history_queryset(company, client_ids=client_ids)
        .values("client_id")
        .annotate(avg_estimated_liters=Avg("estimated_liters"))
    )
    estimated_avg_by_client = {item["client_id"]: item["avg_estimated_liters"] for item in estimated_rows}

    planned_liters_by_client = {}
    for client_id in client_ids:
        confirmed_avg = confirmed_avg_by_client.get(client_id)
        if confirmed_avg is not None:
            planned_liters_by_client[client_id] = Decimal(confirmed_avg).quantize(Decimal("0.01"))
            continue

        estimated_avg = estimated_avg_by_client.get(client_id)
        if estimated_avg is not None:
            planned_liters_by_client[client_id] = Decimal(estimated_avg).quantize(Decimal("0.01"))
            continue

        planned_liters_by_client[client_id] = Decimal("60.00")

    return planned_liters_by_client


def _collection_scope_for_company(company, prefix=""):
    return (
        Q(**{f"{prefix}route_day_client__route_day__route__company": company})
        | Q(**{f"{prefix}route_day_client__isnull": True, f"{prefix}worker__company": company})
    )


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
    logging.info(f"[route_utils - _apply_auto_estimate_without_contact] Solicitud {collection_request.id} autoestimada sin contacto con {estimated} litros")


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
                    logging.info(f"[route_utils - _schedule_collection_request] Task anterior {old_task_id} revocada para solicitud {collection_request.id}")
                except Exception as e:
                    logging.warning(f"[route_utils - _schedule_collection_request] No se pudo revocar task anterior {old_task_id} para solicitud {collection_request.id}: {str(e)}")

            if updated_expiration:
                collection_request.save(update_fields=["expires_at", "modified_date"])

            if collection_request.status in [CollectionRequestStatus.ANSWERED, CollectionRequestStatus.MANUAL]:
                logging.info(f"[route_utils - _schedule_collection_request] Solicitud {collection_request.id} conservada en estado {collection_request.status} sin notificacion")
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
                        logging.info(f"[route_utils - _schedule_collection_request] Task anterior {old_task_id} revocada para solicitud {collection_request.id}")
                    except Exception as e:
                        logging.warning(f"[route_utils - _schedule_collection_request] No se pudo revocar task anterior {old_task_id} para solicitud {collection_request.id}: {str(e)}")
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


def _route_day_client_has_location(row):
    return bool(getattr(row.client, "location", None))


def _planned_liters_for_optimization(row, planned_liters_by_row=None):
    if planned_liters_by_row and row.id in planned_liters_by_row:
        return Decimal(planned_liters_by_row[row.id] or 0).quantize(Decimal("0.01"))
    return _planned_stop_liters(row).quantize(Decimal("0.01"))


def _split_route_day_clients_by_capacity(route_day_clients, capacity_limit, planned_liters_by_row=None):
    if not route_day_clients:
        return []

    capacity_limit = Decimal(capacity_limit or 0).quantize(Decimal("0.01"))
    if capacity_limit <= 0:
        return [route_day_clients]

    segments = []
    current_segment = []
    current_liters = Decimal("0.00")

    for row in route_day_clients:
        row_liters = _planned_liters_for_optimization(row, planned_liters_by_row)
        if current_segment and current_liters > 0 and current_liters + row_liters > capacity_limit:
            segments.append(current_segment)
            current_segment = []
            current_liters = Decimal("0.00")

        current_segment.append(row)
        current_liters += row_liters

    if current_segment:
        segments.append(current_segment)

    return segments


def _merge_optimized_located_rows_preserving_unlocated(segment_rows, optimized_located_rows):
    optimized_iter = iter(optimized_located_rows)
    merged = []
    for row in segment_rows:
        if _route_day_client_has_location(row):
            merged.append(next(optimized_iter))
        else:
            merged.append(row)
    return merged


def _optimize_route_day_segment_with_google(route_day, segment_rows, hub, api_key, segment_number):
    located_rows = [row for row in segment_rows if _route_day_client_has_location(row)]
    if len(located_rows) < 2:
        return segment_rows

    origin = f"{hub.location.y},{hub.location.x}"
    waypoints = "|".join(f"{row.client.location.y},{row.client.location.x}" for row in located_rows)

    params = {
        "origin": origin,
        "destination": origin,
        "waypoints": f"optimize:true|{waypoints}",
        "key": api_key,
    }

    try:
        response = requests.get("https://maps.googleapis.com/maps/api/directions/json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logging.error(f"[route_utils - optimize_route_day_with_google] Error consultando Google Directions API en route_day {route_day.id}, segmento {segment_number}: {exc}")
        return segment_rows

    routes = data.get("routes") or []
    if not routes:
        google_status = data.get("status")
        google_error = data.get("error_message")
        if google_status or google_error:
            logging.warning(f"[route_utils - optimize_route_day_with_google] Segmento {segment_number} no optimizado en route_day {route_day.id}: status={google_status}, error={google_error}")
        else:
            logging.warning(f"[route_utils - optimize_route_day_with_google] Segmento {segment_number} no optimizado en route_day {route_day.id}: Google Directions sin rutas validas")
        return segment_rows

    waypoint_order = routes[0].get("waypoint_order", [])
    valid_order = (
        len(waypoint_order) == len(located_rows)
        and all(isinstance(index, int) and 0 <= index < len(located_rows) for index in waypoint_order)
    )
    if not valid_order:
        logging.warning(f"[route_utils - optimize_route_day_with_google] Segmento {segment_number} no optimizado en route_day {route_day.id}: respuesta de Google invalida")
        return segment_rows

    optimized_located_rows = [located_rows[index] for index in waypoint_order]
    return _merge_optimized_located_rows_preserving_unlocated(segment_rows, optimized_located_rows)


def _persist_route_day_client_order(route_day, ordered_rows):
    desired_orders = {row.id: index for index, row in enumerate(ordered_rows, start=1)}
    rows_to_update = [row for row in ordered_rows if row.order != desired_orders[row.id]]
    updated_rows = len(rows_to_update)

    if updated_rows > 0:
        with transaction.atomic():
            max_order = RouteDayClient.objects.filter(route_day_id=route_day.id).aggregate(max_order=Max("order")).get("max_order") or 0
            temp_base = int(max_order) + len(ordered_rows) + 100

            for index, row in enumerate(rows_to_update, start=1):
                row.order = temp_base + index
            RouteDayClient.objects.bulk_update(rows_to_update, ["order"])

            for row in rows_to_update:
                row.order = desired_orders[row.id]
            RouteDayClient.objects.bulk_update(rows_to_update, ["order"])

    return updated_rows


def optimize_route_day_with_google(route_day, planned_liters_by_row=None):
    route_day_clients = list(route_day.ordered_clients.select_related("client").order_by("order"))
    if len(route_day_clients) < 2:
        logging.info(f"[route_utils - optimize_route_day_with_google] Optimizacion Google no aplicada en route_day {route_day.id}: menos de 2 paradas")
        return route_day_clients

    located_rows = [row for row in route_day_clients if _route_day_client_has_location(row)]
    if len(located_rows) < 2:
        logging.info(f"[route_utils - optimize_route_day_with_google] Optimizacion Google no aplicada en route_day {route_day.id}: menos de 2 paradas con ubicacion")
        return route_day_clients

    skipped_without_location = len(route_day_clients) - len(located_rows)
    if skipped_without_location > 0:
        logging.warning(f"[route_utils - optimize_route_day_with_google] {skipped_without_location} paradas sin ubicacion se conservaran en su posicion relativa en route_day {route_day.id}")

    hub = CompanyHub.objects.filter(company=route_day.route.company, location__isnull=False).first()
    if not hub:
        logging.info(f"[route_utils - optimize_route_day_with_google] Optimizacion Google no aplicada en route_day {route_day.id}: no hay hub para company {route_day.route.company_id}")
        return route_day_clients

    api_key = settings.GOOGLE_MAPS_API_KEY if hasattr(settings, "GOOGLE_MAPS_API_KEY") else ""
    if not api_key:
        logging.warning(f"[route_utils - optimize_route_day_with_google] Optimizacion Google no aplicada en route_day {route_day.id}: GOOGLE_MAPS_API_KEY no configurada")
        return route_day_clients

    capacity_limit = Decimal(route_day.daily_capacity_liters or 0)
    segments = _split_route_day_clients_by_capacity(route_day_clients, capacity_limit, planned_liters_by_row=planned_liters_by_row)
    optimized = []
    for segment_number, segment_rows in enumerate(segments, start=1):
        optimized.extend(_optimize_route_day_segment_with_google(route_day, segment_rows, hub, api_key, segment_number))

    if len(optimized) != len(route_day_clients):
        logging.warning(f"[route_utils - optimize_route_day_with_google] Optimizacion Google no aplicada en route_day {route_day.id}: resultado segmentado invalido")
        return route_day_clients

    updated_rows = _persist_route_day_client_order(route_day, optimized)

    if updated_rows == 0:
        logging.info(f"[route_utils - optimize_route_day_with_google] Optimizacion Google sin cambios en route_day {route_day.id}")
    else:
        logging.info(f"[route_utils - optimize_route_day_with_google] Optimizacion Google segmentada aplicada en route_day {route_day.id}: {updated_rows} paradas reordenadas en {len(segments)} segmentos")

    return optimized


def generate_route_day_clients(route_day, regenerate=False, reserved_client_ids=None, auto_estimate_without_contact=False, optimize_with_google=True, max_clients_per_day=MAX_CLIENTS_PER_DAY):
    try:
        reserved_client_ids = reserved_client_ids or set()

        if not _is_route_day_generation_mutable(route_day):
            if regenerate:
                logging.warning(f"[route_utils - generate_route_day_clients] Regeneracion bloqueada para route_day {route_day.id} con estado {route_day.status}")
                raise ValueError(ROUTE_DAY_GENERATION_LOCKED)
            logging.info(f"[route_utils - generate_route_day_clients] Generacion omitida para route_day {route_day.id} con estado {route_day.status}")
            return list(route_day.ordered_clients.select_related("client").order_by("order"))

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
                logging.warning(f"[route_utils - generate_route_day_clients] Eliminadas {len(duplicate_row_ids)} paradas duplicadas en route_day {route_day.id}")

        if not zone_day:
            logging.info(f"[route_utils - generate_route_day_clients] Sin paradas en route_day {route_day.id}: no hay RouteZoneDay configurado para weekday {route_day.weekday}")
            return []

        zones = list(zone_day.zones.all())
        if not zones:
            logging.info(f"[route_utils - generate_route_day_clients] Sin paradas en route_day {route_day.id}: RouteZoneDay sin zonas asignadas")
            return []

        zone_filters = [Q(location__within=zone.polygon) for zone in zones if zone.polygon]
        if not zone_filters:
            logging.info(f"[route_utils - generate_route_day_clients] Sin paradas en route_day {route_day.id}: zonas sin geometria valida")
            return []

        spatial_q = reduce(lambda acc, item: acc | item, zone_filters)
        clients_qs = (
            Client.objects
            .filter(companies=route_day.route.company, location__isnull=False)
            .filter(spatial_q)
            .annotate(
                last_collection_date=Max(
                    "collections__collection_date",
                    filter=(
                        Q(collections__collection_date__lt=route_day.date)
                        & ~Q(collections__status=CollectionStatus.CANCELED)
                        & _collection_scope_for_company(route_day.route.company, prefix="collections__")
                    ),
                )
            )
            .annotate(
                last_planned_date=Max(
                    "routedayclient__route_day__date",
                    filter=(
                        Q(routedayclient__route_day__date__lt=route_day.date)
                        & ~Q(routedayclient__route_day__status=RouteDayStatus.CANCELED)
                        & Q(routedayclient__route_day__route__company=route_day.route.company)
                    ),
                )
            )
            .distinct()
        )

        due_clients = [
            client for client in clients_qs
            if _is_client_due(
                client,
                route_day.date,
                last_collection_date=client.last_collection_date,
                last_planned_date=client.last_planned_date,
            )
        ]
        if not due_clients:
            candidate_clients = clients_qs.count()
            logging.info(f"[route_utils - generate_route_day_clients] Sin paradas en route_day {route_day.id}: 0 clientes por frecuencia en fecha {route_day.date} (candidatos en zona: {candidate_clients})")

        def _effective_reference_date(client):
            reference_date = client.last_collection_date
            if client.last_planned_date and (not reference_date or client.last_planned_date > reference_date):
                reference_date = client.last_planned_date
            return reference_date

        due_clients = sorted(
            due_clients,
            key=lambda item: (
                _effective_reference_date(item) is not None,
                _effective_reference_date(item) or route_day.date,
                item.id,
            ),
        )

        due_client_ids = [item.id for item in due_clients]
        planned_liters_by_client = _planned_liters_by_client_for_company(route_day.route.company, due_client_ids)

        current_rows = list(route_day.ordered_clients.select_related("collection_request").all().order_by("order"))
        planned_liters_by_row = {row.id: _planned_stop_liters(row) for row in current_rows}
        existing_client_ids = set(item.client_id for item in current_rows)
        max_clients_limit = int(max_clients_per_day or 0)
        capacity_limit = Decimal(route_day.daily_capacity_liters or 0)
        current_planned_liters = sum((_planned_stop_liters(item) for item in current_rows), Decimal("0.00"))

        next_order = int(route_day.ordered_clients.aggregate(max_order=Max("order"))["max_order"] or 0) + 1
        skipped_by_capacity = 0
        created_rows = 0

        for client in due_clients:
            if client.id in existing_client_ids:
                continue
            if client.id in reserved_client_ids:
                continue
            if max_clients_limit > 0 and (len(existing_client_ids) >= max_clients_limit):
                break

            planned_liters = planned_liters_by_client.get(client.id, Decimal("60.00"))
            if capacity_limit > 0 and (current_planned_liters + planned_liters > capacity_limit):
                skipped_by_capacity += 1
                continue

            route_day_client = RouteDayClient.objects.create(route_day=route_day, client=client, order=next_order)
            planned_liters_by_row[route_day_client.id] = planned_liters
            next_order += 1
            created_rows += 1
            existing_client_ids.add(client.id)
            current_planned_liters += planned_liters

        if max_clients_limit > 0 and len(existing_client_ids) >= max_clients_limit:
            logging.info(f"[route_utils - generate_route_day_clients] Limite max_clients_per_day alcanzado en route_day {route_day.id}: {max_clients_limit}")
        if skipped_by_capacity > 0:
            logging.info(f"[route_utils - generate_route_day_clients] {skipped_by_capacity} clientes omitidos por capacidad en route_day {route_day.id}")
        if created_rows > 0:
            logging.info(f"[route_utils - generate_route_day_clients] {created_rows} paradas creadas en route_day {route_day.id}")

        if optimize_with_google:
            optimized_rows = optimize_route_day_with_google(route_day, planned_liters_by_row=planned_liters_by_row)
        else:
            optimized_rows = list(route_day.ordered_clients.select_related("client").order_by("order"))
            logging.info(f"[route_utils - generate_route_day_clients] Optimizacion Google desactivada para route_day {route_day.id}, se conserva orden actual")
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
        logging.error(f"[route_utils - generate_route_day_clients] Error generando paradas para route_day {route_day.id}: {str(e)}")
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
        if route_day.route.worker_id == user.worker_profile.id:
            return user.worker_profile

    if worker_id:
        worker = route_day.route.worker
        if worker and worker.id == worker_id and worker.company_id == route_day.route.company_id:
            return worker

    worker = route_day.route.worker
    if worker and worker.company_id == route_day.route.company_id:
        return worker
    return None


@transaction.atomic
def complete_route_day_client(route_day, route_day_client, user, payload):
    if route_day.status != RouteDayStatus.IN_PROGRESS:
        raise ValueError(ROUTE_DAY_STOP_ROUTE_NOT_STARTED)

    existing_collection = Collection.objects.filter(route_day_client=route_day_client).order_by("-id").first()
    if existing_collection:
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
    resolved_price = resolve_default_collection_price_per_liter(company=route_day.route.company)
    price_per_liter = resolved_price if resolved_price is not None else Decimal("0.00")
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


def _latest_route_day_client_collection(row):
    prefetched_objects = getattr(row, "_prefetched_objects_cache", {})
    if "collections" in prefetched_objects:
        row_collections = list(prefetched_objects["collections"])
    else:
        row_collections = list(row.collections.all())

    if not row_collections:
        return None
    return max(row_collections, key=lambda item: item.id)


def build_route_day_operational_plan(route_day, ordered_clients=None):
    ordered_rows = list(ordered_clients) if ordered_clients is not None else list(
        route_day.ordered_clients
        .select_related("collection_request")
        .prefetch_related("collections")
        .order_by("order")
    )
    ordered_rows = sorted(ordered_rows, key=lambda item: item.order)

    capacity_limit = Decimal(route_day.daily_capacity_liters or 0).quantize(Decimal("0.01"))
    segments = []
    current_segment = None
    total_planned_liters = Decimal("0.00")
    total_registered_non_canceled_liters = Decimal("0.00")

    for row in ordered_rows:
        stop_liters = _planned_stop_liters(row).quantize(Decimal("0.01"))
        latest_collection = _latest_route_day_client_collection(row)
        is_registered = latest_collection is not None
        is_canceled = bool(latest_collection and latest_collection.status == CollectionStatus.CANCELED)

        if (
            current_segment
            and capacity_limit > 0
            and current_segment["planned_load_liters"] > 0
            and current_segment["planned_load_liters"] + stop_liters > capacity_limit
        ):
            segments.append(current_segment)
            current_segment = None

        if current_segment is None:
            current_segment = {
                "number": len(segments) + 1,
                "planned_load_liters": Decimal("0.00"),
                "current_load_liters": Decimal("0.00"),
                "planned_stops_count": 0,
                "registered_stops": 0,
                "completed_stops": 0,
                "canceled_stops": 0,
                "pending_stops": 0,
                "first_pending_route_day_client_id": None,
                "stop_route_day_client_ids": [],
                "stop_orders": [],
            }

        current_segment["planned_load_liters"] += stop_liters
        current_segment["planned_stops_count"] += 1
        current_segment["stop_route_day_client_ids"].append(row.id)
        current_segment["stop_orders"].append(row.order)

        if is_registered:
            current_segment["registered_stops"] += 1
            if is_canceled:
                current_segment["canceled_stops"] += 1
            else:
                current_segment["completed_stops"] += 1
                current_segment["current_load_liters"] += stop_liters
                total_registered_non_canceled_liters += stop_liters
        else:
            current_segment["pending_stops"] += 1
            if current_segment["first_pending_route_day_client_id"] is None:
                current_segment["first_pending_route_day_client_id"] = row.id

        total_planned_liters += stop_liters

    if current_segment:
        segments.append(current_segment)

    for segment in segments:
        segment["planned_load_liters"] = segment["planned_load_liters"].quantize(Decimal("0.01"))
        segment["current_load_liters"] = segment["current_load_liters"].quantize(Decimal("0.01"))
        if capacity_limit > 0:
            remaining_capacity = capacity_limit - segment["current_load_liters"]
            if remaining_capacity < 0:
                remaining_capacity = Decimal("0.00")
            segment["remaining_capacity_liters"] = remaining_capacity.quantize(Decimal("0.01"))
        else:
            segment["remaining_capacity_liters"] = None

    active_segment = next((segment for segment in segments if segment["pending_stops"] > 0), None)
    if active_segment is None and segments:
        active_segment = segments[-1]

    return {
        "capacity_liters": capacity_limit if capacity_limit > 0 else None,
        "planned_load_liters": total_planned_liters.quantize(Decimal("0.01")),
        "registered_load_liters": total_registered_non_canceled_liters.quantize(Decimal("0.01")),
        "segments_count": len(segments),
        "returns_to_hub_count": max(len(segments) - 1, 0),
        "requires_hub_return": len(segments) > 1,
        "active_segment_number": active_segment["number"] if active_segment else None,
        "active_segment_route_day_client_id": active_segment["first_pending_route_day_client_id"] if active_segment else None,
        "active_segment_current_load_liters": active_segment["current_load_liters"] if active_segment else Decimal("0.00"),
        "active_segment_remaining_capacity_liters": active_segment["remaining_capacity_liters"] if active_segment else None,
        "segments": segments,
    }


def _chunk_list(items, chunk_size):
    chunk_size = max(int(chunk_size or 1), 1)
    return [items[index:index + chunk_size] for index in range(0, len(items), chunk_size)]


def _build_google_navigation_url(origin, waypoint_points):
    params = {
        "api": "1",
        "origin": origin,
        "destination": origin,
        "travelmode": "driving",
    }
    if waypoint_points:
        params["waypoints"] = "|".join(waypoint_points)
    return f"https://www.google.com/maps/dir/?{urlencode(params, safe='|,')}"


def _route_day_navigation_segment_points(route_day):
    route_day_clients = list(
        route_day.ordered_clients
        .select_related("client", "collection_request")
        .prefetch_related("collections")
        .filter(client__location__isnull=False)
        .order_by("order")
    )
    if not route_day_clients:
        raise ValueError(ROUTE_DAY_GOOGLE_NAVIGATION_EMPTY)

    hub = CompanyHub.objects.filter(company=route_day.route.company, location__isnull=False).first()
    if not hub:
        raise ValueError(ROUTE_DAY_GOOGLE_HUB_REQUIRED)

    operational_plan = build_route_day_operational_plan(route_day, ordered_clients=route_day_clients)
    segment_ids = [segment["stop_route_day_client_ids"] for segment in operational_plan["segments"]]
    route_day_clients_by_id = {item.id: item for item in route_day_clients}
    segment_stop_points = []

    for stop_ids in segment_ids:
        segment_points = []
        for stop_id in stop_ids:
            row = route_day_clients_by_id.get(stop_id)
            if not row:
                continue
            segment_points.append(f"{row.client.location.y},{row.client.location.x}")
        if segment_points:
            segment_stop_points.append(segment_points)

    if not segment_stop_points:
        raise ValueError(ROUTE_DAY_GOOGLE_NAVIGATION_EMPTY)

    origin = f"{hub.location.y},{hub.location.x}"
    return origin, segment_stop_points


def get_route_day_google_navigation_urls(route_day, max_waypoints=GOOGLE_MAPS_NAVIGATION_MAX_WAYPOINTS):
    origin, segment_stop_points = _route_day_navigation_segment_points(route_day)

    waypoint_points = []
    for segment_index, segment_points in enumerate(segment_stop_points):
        waypoint_points.extend(segment_points)
        if segment_index < len(segment_stop_points) - 1:
            waypoint_points.append(origin)

    max_waypoints = max(int(max_waypoints or GOOGLE_MAPS_NAVIGATION_MAX_WAYPOINTS), 1)
    if len(waypoint_points) <= max_waypoints:
        return [_build_google_navigation_url(origin, waypoint_points)]

    urls = []
    for segment_points in segment_stop_points:
        for chunk in _chunk_list(segment_points, max_waypoints):
            urls.append(_build_google_navigation_url(origin, chunk))

    return urls


def get_route_day_google_navigation_url(route_day):
    return get_route_day_google_navigation_urls(route_day)[0]


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


def _is_route_day_generation_mutable(route_day):
    has_execution_trace = (
        bool(route_day.started_at)
        or bool(route_day.finished_at)
        or Collection.objects.filter(route_day_client__route_day=route_day).exists()
    )
    if has_execution_trace:
        return False
    return route_day.status in [RouteDayStatus.PLANNED, RouteDayStatus.CANCELED]


def _ensure_week_regeneration_allowed(route, week_start_date, week_end_date):
    week_route_days = list(
        RouteDay.objects
        .filter(route=route, date__gte=week_start_date, date__lte=week_end_date)
        .order_by("date")
    )
    locked_days = [route_day.date for route_day in week_route_days if not _is_route_day_generation_mutable(route_day)]
    if locked_days:
        logging.warning(f"[route_utils - _ensure_week_regeneration_allowed] Regeneracion bloqueada para ruta {route.id} por route_days no mutables en fechas {locked_days}")
        raise ValueError(ROUTE_WEEK_REGENERATION_LOCKED)


def get_operational_week_start(route, reference_date):
    delta_days = (reference_date.weekday() - route.week_start) % 7
    return reference_date - timedelta(days=delta_days)


def _resolve_route_default_capacity_liters(route):
    try:
        if hasattr(route, "_default_capacity_liters_cache"):
            return route._default_capacity_liters_cache

        worker = route.worker
        if worker and hasattr(worker, "truck") and worker.truck and worker.truck.capacity_liters is not None:
            route._default_capacity_liters_cache = worker.truck.capacity_liters
            return route._default_capacity_liters_cache
        route._default_capacity_liters_cache = None
        return route._default_capacity_liters_cache
    except Exception as e:
        logging.warning(f"[route_utils - _resolve_route_default_capacity_liters] No se pudo resolver capacidad por defecto para ruta {route.id}: {str(e)}")
        return None


def resolve_route_day_capacity_liters(route_day):
    try:
        if route_day.daily_capacity_liters is not None:
            return route_day.daily_capacity_liters
        return _resolve_route_default_capacity_liters(route_day.route)
    except Exception as e:
        logging.warning(f"[route_utils - resolve_route_day_capacity_liters] No se pudo resolver capacidad para route_day {route_day.id}: {str(e)}")
        return route_day.daily_capacity_liters


def resolve_route_default_capacity_liters(route):
    try:
        return _resolve_route_default_capacity_liters(route)
    except Exception as e:
        logging.warning(f"[route_utils - resolve_route_default_capacity_liters] No se pudo resolver capacidad por defecto para ruta {route.id}: {str(e)}")
        return None


def _ensure_route_day_capacity_liters(route_day):
    if route_day.daily_capacity_liters is not None:
        return route_day.daily_capacity_liters

    resolved_capacity = _resolve_route_default_capacity_liters(route_day.route)
    if resolved_capacity is None:
        return None

    route_day.daily_capacity_liters = resolved_capacity
    route_day.save(update_fields=["daily_capacity_liters"])
    logging.info(f"[route_utils - _ensure_route_day_capacity_liters] Capacidad {resolved_capacity} L asignada a route_day {route_day.id}")
    return route_day.daily_capacity_liters


@transaction.atomic
def ensure_route_day_for_date(route, target_date, optimize_with_google=False):
    try:
        locked_route = Route.objects.select_for_update().get(id=route.id)
        if not _is_route_date_in_range(locked_route, target_date):
            return None
        if not _is_weekday_enabled(locked_route, target_date.weekday()):
            return None

        route_day, created = RouteDay.objects.get_or_create(route=locked_route, date=target_date)
        _ensure_route_day_capacity_liters(route_day)

        if created or not route_day.ordered_clients.exists():
            generate_route_day_clients(route_day, regenerate=False, optimize_with_google=optimize_with_google)
            logging.info(f"[route_utils - ensure_route_day_for_date] RouteDay {route_day.id} asegurado para fecha {target_date}")

        return route_day
    except Exception as e:
        logging.error(f"[route_utils - ensure_route_day_for_date] Error asegurando route_day para ruta {route.id} y fecha {target_date}: {str(e)}")
        raise


@transaction.atomic
def generate_week_for_route(route, week_start_date, regenerate=False, daily_capacity_liters=None, days=None, auto_estimate_without_contact=False, max_clients_per_day=10, optimize_with_google=True):
    lock_key = f"route_week_generation_lock_{route.id}_{week_start_date.isoformat()}"
    if not cache.add(lock_key, "1", timeout=300):
        logging.warning(f"[route_utils - generate_week_for_route] Lock activo para ruta {route.id} y semana {week_start_date}")
        raise ValueError(ROUTE_WEEK_GENERATION_IN_PROGRESS)

    try:
        locked_route = Route.objects.select_for_update().get(id=route.id)
        week_end_date = week_start_date + timedelta(days=6)
        if week_end_date < locked_route.start_date or (locked_route.end_date and week_start_date > locked_route.end_date):
            logging.warning(f"[route_utils - generate_week_for_route] Semana {week_start_date} fuera de rango para ruta {locked_route.id}")
            raise ValueError(ROUTE_WEEK_OUTSIDE_ROUTE_RANGE)
        if regenerate:
            _ensure_week_regeneration_allowed(locked_route, week_start_date, week_end_date)

        days = days or []
        capacities_by_date = {item["date"]: item["daily_capacity_liters"] for item in days}
        route_days = []
        week_assigned_client_ids = set()
        if not regenerate:
            existing_week_client_ids = (
                RouteDayClient.objects
                .filter(route_day__route=locked_route, route_day__date__gte=week_start_date, route_day__date__lte=week_end_date)
                .values_list("client_id", flat=True)
            )
            week_assigned_client_ids = set(existing_week_client_ids)
        for i in range(7):
            target_date = week_start_date + timedelta(days=i)
            weekday = target_date.weekday()

            if not _is_route_date_in_range(locked_route, target_date):
                continue

            if not _is_weekday_enabled(locked_route, weekday):
                continue

            route_day, _ = RouteDay.objects.get_or_create(route=locked_route, date=target_date)

            if not _is_route_day_generation_mutable(route_day):
                logging.info(f"[route_utils - generate_week_for_route] RouteDay {route_day.id} preservado en generacion semanal por estado {route_day.status}")
                week_assigned_client_ids.update(route_day.ordered_clients.values_list("client_id", flat=True))
                route_days.append(route_day)
                continue

            if daily_capacity_liters is not None:
                route_day.daily_capacity_liters = daily_capacity_liters
                route_day.save(update_fields=["daily_capacity_liters"])
            elif target_date in capacities_by_date:
                route_day.daily_capacity_liters = capacities_by_date[target_date]
                route_day.save(update_fields=["daily_capacity_liters"])
            else:
                _ensure_route_day_capacity_liters(route_day)

            current_day_client_ids = set(route_day.ordered_clients.values_list("client_id", flat=True))
            if regenerate:
                reserved_client_ids = set(week_assigned_client_ids)
            else:
                reserved_client_ids = set(week_assigned_client_ids) - current_day_client_ids

            generate_route_day_clients(
                route_day,
                regenerate=regenerate,
                reserved_client_ids=reserved_client_ids,
                auto_estimate_without_contact=auto_estimate_without_contact,
                optimize_with_google=optimize_with_google,
                max_clients_per_day=max_clients_per_day,
            )
            updated_day_client_ids = set(route_day.ordered_clients.values_list("client_id", flat=True))
            week_assigned_client_ids.update(updated_day_client_ids)
            route_days.append(route_day)

        logging.info(f"[route_utils - generate_week_for_route] Semana generada para ruta {locked_route.id} con {len(route_days)} route_days")
        return route_days
    except Exception as e:
        logging.error(f"[route_utils - generate_week_for_route] Error generando semana para ruta {route.id}: {str(e)}")
        raise
    finally:
        cache.delete(lock_key)


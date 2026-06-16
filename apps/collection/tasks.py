from decimal import Decimal
import logging
import os

from celery import shared_task
from django.db.models import Avg
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from apps.base.literals import COLLECTION_REQUEST_NOTIFY_BODY, COLLECTION_REQUEST_NOTIFY_SUBJECT
from apps.base.enums import CollectionRequestStatus, PlannedSource, CollectionStatus
from apps.base.utils import send_email_google_api
from apps.collection.models import CollectionRequest, Collection
from apps.base.logger import configure_logging

configure_logging()


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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_estimate_collection_request_liters(self, collection_request_id):
    try:
        try:
            collection_request = CollectionRequest.objects.select_related(
                "route_day_client",
                "route_day_client__client",
            ).get(id=collection_request_id)
        except CollectionRequest.DoesNotExist:
            logging.warning(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request_id} no existe, se omite autoestimacion")
            return

        if collection_request.status != CollectionRequestStatus.PENDING:
            logging.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} en estado {collection_request.status}, no se autoestima")
            return

        if timezone.now() < collection_request.expires_at:
            logging.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} aun no expirada, se omite")
            return

        client_id = collection_request.route_day_client.client_id

        historical_avg = (
            Collection.objects
            .filter(client_id=client_id)
            .exclude(status=CollectionStatus.CANCELED)
            .aggregate(avg_liters=Avg("net_liters"))
            .get("avg_liters")
        )

        if historical_avg is not None:
            estimated = Decimal(historical_avg).quantize(Decimal("0.01"))
        elif collection_request.container_number:
            estimated = collection_request.compute_client_liters() or Decimal("60.00")
        else:
            estimated = Decimal("60.00")

        collection_request.estimated_liters = estimated
        if collection_request.final_liters is None:
            collection_request.final_liters = estimated
        if not collection_request.final_source:
            collection_request.final_source = PlannedSource.AUTO

        collection_request.status = CollectionRequestStatus.AUTO_ESTIMATED
        collection_request.save(
            update_fields=[
                "estimated_liters",
                "final_liters",
                "final_source",
                "status",
                "modified_date",
            ]
        )
        logging.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} autoestimada con {estimated} litros")
    except Exception as e:
        logging.error(f"[collection_tasks - auto_estimate_collection_request_liters] Error en autoestimacion para solicitud {collection_request_id}: {str(e)}")
        raise self.retry(exc=e)


@shared_task
def notify_collection_request_created(collection_request_id):
    try:
        if not _gmail_ready_for_notifications():
            logging.warning(f"[collection_tasks - notify_collection_request_created] Notificacion omitida por Gmail API no configurada para solicitud {collection_request_id}")
            return

        try:
            collection_request = CollectionRequest.objects.select_related(
                "route_day_client",
                "route_day_client__client",
                "route_day_client__client__user",
                "route_day_client__route_day",
                "route_day_client__route_day__route",
            ).get(id=collection_request_id)
        except CollectionRequest.DoesNotExist:
            logging.warning(f"[collection_tasks - notify_collection_request_created] Solicitud {collection_request_id} no existe, no se notifica")
            return

        email = collection_request.route_day_client.client.user.email
        if not email:
            logging.warning(f"[collection_tasks - notify_collection_request_created] Cliente sin email para solicitud {collection_request.id}")
            return

        route_day = collection_request.route_day_client.route_day
        subject = COLLECTION_REQUEST_NOTIFY_SUBJECT
        message = COLLECTION_REQUEST_NOTIFY_BODY.format(
            route_name=route_day.route.name,
            route_date=route_day.date,
            expires_at=collection_request.expires_at,
        )
        html_message = render_to_string(
            "email/collection_request_created.html",
            {
                "client_name": collection_request.route_day_client.client.name,
                "route_name": route_day.route.name,
                "route_date": route_day.date,
                "expires_at": collection_request.expires_at,
                "year": timezone.now().year,
            },
        )
        text_message = strip_tags(html_message) or message
        sent = send_email_google_api(
            to_email=email,
            subject=subject,
            text_message=text_message,
            html_message=html_message,
        )
        if sent:
            logging.info(f"[collection_tasks - notify_collection_request_created] Notificacion enviada a {email} para solicitud {collection_request.id}")
        else:
            logging.warning(f"[collection_tasks - notify_collection_request_created] No se pudo enviar notificacion para solicitud {collection_request.id}")
    except Exception as e:
        logging.error(f"[collection_tasks - notify_collection_request_created] Error enviando notificacion para solicitud {collection_request_id}: {str(e)}")
        return


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_expired_collection_requests(self, batch_size=200):
    try:
        now = timezone.now()
        pending_requests = list(
            CollectionRequest.objects
            .filter(status=CollectionRequestStatus.PENDING, expires_at__lte=now)
            .order_by("expires_at")[:batch_size]
        )

        if not pending_requests:
            logging.info("[collection_tasks - process_expired_collection_requests] No hay solicitudes pendientes expiradas para procesar")
            return

        for collection_request in pending_requests:
            auto_estimate_collection_request_liters.delay(collection_request.id)

        logging.info(f"[collection_tasks - process_expired_collection_requests] Encoladas {len(pending_requests)} solicitudes expiradas para autoestimacion")
    except Exception as e:
        logging.error(f"[collection_tasks - process_expired_collection_requests] Error procesando solicitudes expiradas: {str(e)}")
        raise self.retry(exc=e)

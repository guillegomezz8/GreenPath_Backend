from decimal import Decimal
import logging

from celery import shared_task
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.base.literals import COLLECTION_REQUEST_NOTIFY_BODY, COLLECTION_REQUEST_NOTIFY_SUBJECT
from apps.base.enums import CollectionRequestStatus, PlannedSource, CollectionStatus
from apps.collection.models import CollectionRequest, Collection

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_estimate_collection_request_liters(self, collection_request_id):
    try:
        try:
            collection_request = CollectionRequest.objects.select_related(
                "route_day_client",
                "route_day_client__client",
            ).get(id=collection_request_id)
        except CollectionRequest.DoesNotExist:
            logger.warning(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request_id} no existe, se omite autoestimacion")
            return

        if collection_request.status != CollectionRequestStatus.PENDING:
            logger.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} en estado {collection_request.status}, no se autoestima")
            return

        if timezone.now() < collection_request.expires_at:
            logger.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} aun no expirada, se omite")
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
        logger.info(f"[collection_tasks - auto_estimate_collection_request_liters] Solicitud {collection_request.id} autoestimada con {estimated} litros")
    except Exception as e:
        logger.error(f"[collection_tasks - auto_estimate_collection_request_liters] Error en autoestimacion para solicitud {collection_request_id}: {str(e)}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_collection_request_created(self, collection_request_id):
    try:
        try:
            collection_request = CollectionRequest.objects.select_related(
                "route_day_client",
                "route_day_client__client",
                "route_day_client__client__user",
                "route_day_client__route_day",
                "route_day_client__route_day__route",
            ).get(id=collection_request_id)
        except CollectionRequest.DoesNotExist:
            logger.warning(f"[collection_tasks - notify_collection_request_created] Solicitud {collection_request_id} no existe, no se notifica")
            return

        client_user = collection_request.route_day_client.client.user if hasattr(collection_request.route_day_client.client, "user") else None
        email = client_user.email if client_user else None
        if not email:
            logger.warning(f"[collection_tasks - notify_collection_request_created] Cliente sin email para solicitud {collection_request.id}")
            return
        email_sender = settings.EMAIL_HOST_USER if hasattr(settings, "EMAIL_HOST_USER") else ""
        if not email_sender:
            logger.warning(f"[collection_tasks - notify_collection_request_created] EMAIL_HOST_USER no configurado para solicitud {collection_request.id}")
            return

        route_day = collection_request.route_day_client.route_day
        subject = COLLECTION_REQUEST_NOTIFY_SUBJECT
        message = COLLECTION_REQUEST_NOTIFY_BODY.format(
            route_name=route_day.route.name,
            route_date=route_day.date,
            expires_at=collection_request.expires_at,
        )

        send_mail(subject, message, email_sender, [email], fail_silently=False)
        logger.info(f"[collection_tasks - notify_collection_request_created] Notificacion enviada a {email} para solicitud {collection_request.id}")
    except Exception as e:
        logger.error(f"[collection_tasks - notify_collection_request_created] Error enviando notificacion para solicitud {collection_request_id}: {str(e)}")
        raise self.retry(exc=e)


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
            logger.info("[collection_tasks - process_expired_collection_requests] No hay solicitudes pendientes expiradas para procesar")
            return

        for collection_request in pending_requests:
            auto_estimate_collection_request_liters.delay(collection_request.id)

        logger.info(f"[collection_tasks - process_expired_collection_requests] Encoladas {len(pending_requests)} solicitudes expiradas para autoestimacion")
    except Exception as e:
        logger.error(f"[collection_tasks - process_expired_collection_requests] Error procesando solicitudes expiradas: {str(e)}")
        raise self.retry(exc=e)

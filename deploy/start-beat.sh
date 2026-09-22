#!/bin/sh
set -eu

exec celery -A global beat \
    --loglevel="${CELERY_LOG_LEVEL:-info}" \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

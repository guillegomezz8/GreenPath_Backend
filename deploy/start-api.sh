#!/bin/sh
set -eu

# El volumen de Railway se monta despues de construir la imagen y oculta el
# directorio creado durante el build. Se recrea el destino persistente aqui.
mkdir -p /src/media/exports

python manage.py collectstatic --noinput

exec gunicorn global.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -

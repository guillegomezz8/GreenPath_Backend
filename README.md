# GreenPath Backend

Backend Django para la gestion de recogida de aceite usado.

## Stack

- Python 3.11
- Django + Django REST Framework
- PostgreSQL + PostGIS
- Celery + Redis
- Google Directions API para optimizacion de rutas
- Gmail API para envio de correos operativos

## Modulos principales

- `clients`: clientes, frecuencia de recogida y geolocalizacion.
- `workers`: trabajadores y empresa asociada.
- `trucks`: camiones y conductor asignado.
- `zones`: zonas geograficas de recogida.
- `routes`: rutas plantilla, dias operativos y paradas planificadas.
- `collections`: recogidas reales y solicitudes previas de estimacion.

## Estado actual

Actualmente estan operativos:

- CRUD de clientes, trabajadores, camiones y zonas.
- Configuracion de rutas y zonas por dia.
- Generacion semanal de rutas operativas con `generate-week`.
- Ejecucion de `RouteDay`: iniciar, registrar parada, finalizar y exportar navegacion.
- `CollectionRequest` con expiracion, trazabilidad y tareas Celery.
- Estadisticas y panel operativo ya integrados en la API.

## Flujo de generacion semanal

Endpoint principal:

- `POST /routes/{id}/generate-week/`

Comportamiento actual:

- Crea o reutiliza `RouteDay` dentro de la semana solicitada.
- Genera `RouteDayClient` desde las zonas configuradas para cada weekday.
- Filtra clientes por ubicacion y frecuencia real de recogida.
- Calcula frecuencia e historico previo dentro de la misma empresa de la ruta.
- Evita duplicidades del mismo cliente en la misma semana.
- Respeta `max_clients_per_day`.
- Respeta `daily_capacity_liters` de forma estricta.
- Optimiza el orden con Google Directions si hay `GOOGLE_MAPS_API_KEY`.
- Crea o actualiza `CollectionRequest` por parada.
- Programa autoestimacion con Celery cuando expira la solicitud.

Reglas importantes:

- `generate-week` solo lo puede ejecutar un owner.
- `regenerate=true` solo se permite si toda la semana sigue siendo editable, es decir, sin ejecucion previa ni recogidas asociadas.
- Los `RouteDay` que ya no son editables se preservan y no se tocan en una generacion normal.
- Si ya existe una generacion en curso para la misma ruta y semana, se devuelve conflicto.

## Variables de entorno relevantes

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `GOOGLE_MAPS_API_KEY`
- `GMAIL_FROM`
- `GMAIL_CLIENT_SECRET_JSON`
- `GMAIL_TOKEN_JSON`

Notas:

- `GMAIL_CLIENT_SECRET_JSON` y `GMAIL_TOKEN_JSON` deben ir en una sola linea dentro de `.env`.
- `GMAIL_FROM` no debe llevar espacios antes ni despues del email.

## Desarrollo local

Levantar servicios:

```bash
docker-compose up --build
```

Backend:

- API base: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs/`
- Schema: `http://localhost:8000/schema/`
- Admin: `http://localhost:8000/admin/`

## Documentacion adicional

- `docs/API.md`
- `docs/ROUTE_FLOW.md`
- `docs/FUNCIONAL.md`
- `docs/ARQUITECTURA_TECNICA.md`

## Estado funcional de rutas

El flujo de rutas ya no es solo de planificacion. Tambien cubre:

- inicio de ruta diaria
- registro ordenado de paradas
- cierre de ruta diaria
- navegacion Google Maps
- solicitudes previas al cliente
- autoestimacion si el cliente no responde
- separacion frontend entre `Detalle de ruta` y `Realizar ruta`
- acceso rapido desde dashboard a rutas operativas
- modal responsive compartido para `Generar semana` en listado y detalle

## Pendiente o mejorable

- tests automatizados especificos de generacion semanal y ejecucion de rutas
- endurecer concurrencia distribuida si se despliega con multiples workers web
- ampliar analitica y reporting avanzado

# Flujo de generacion de rutas (Route)

## Estado actual

Si, ahora mismo **si se usa Google para optimizacion**.

La optimizacion principal se hace en:
- `apps/route/utils.py` -> `optimize_route_day_with_google(route_day)`
- Endpoint Google usado: `https://maps.googleapis.com/maps/api/directions/json`
- Se envia `waypoints=optimize:true|...`

Si falla Google, no hay API key o no hay hub, se mantiene el orden actual y el flujo sigue.

## Punto de entrada API

- Endpoint: `POST /routes/{id}/generate-week/`
- View: `apps/route/api/viewsets/route_viewset.py` -> `generate_week`
- Serializer de entrada: `GenerateWeekSerializer`

Validaciones de entrada:
- `week_start_date` obligatorio
- `daily_capacity_liters` global **o** `days[]` por fecha
- no se permiten ambos a la vez
- no se permiten fechas duplicadas en `days`
- fechas de `days` deben estar en la semana (`start + 6`)

Permisos:
- `IsRouteCompanyGenerator` (owner/worker de la empresa de la ruta, o staff/superuser)
- aplicado desde `get_permissions` para `generate_week` y `generate_range_routes`

## Flujo interno principal

Funcion orquestadora:
- `apps/route/utils.py` -> `generate_week_for_route(route, week_start_date, regenerate=False, daily_capacity_liters=None, days=None)`

Pasos:
1. Crea lock temporal por ruta+semana (`cache.add`) para evitar doble generacion concurrente.
2. Bloquea la ruta en DB con `select_for_update`.
3. Valida rango de fechas contra `route.start_date` y `route.end_date`.
4. Recorre 7 dias de la semana solicitada.
5. Omite dias fuera del rango de la ruta y fuera de `week_start/week_end` de la propia ruta.
6. Crea o recupera `RouteDay` (`get_or_create`).
7. Asigna `daily_capacity_liters` (global o por dia).
8. Llama a `generate_route_day_clients(...)` para generar y ordenar paradas.
9. Devuelve lista de `RouteDay` generados.
10. Libera lock.

## Generacion de paradas (RouteDayClient)

Funcion:
- `apps/route/utils.py` -> `generate_route_day_clients(route_day, regenerate=False, reserved_client_ids=None)`

Pasos:
1. Busca configuracion de zonas de ese weekday (`RouteZoneDay`).
2. Si `regenerate=True`:
- revoca tareas de `CollectionRequest` existentes
- borra paradas anteriores del dia
3. Si hay `reserved_client_ids` (clientes ya planificados en la semana), elimina duplicados existentes de ese dia.
4. Construye filtro espacial OR con `location__within` para todas las zonas del dia.
5. Busca clientes de la empresa con geolocalizacion.
6. Anota `last_collection_date` por cliente para evitar N+1.
7. Filtra clientes "due" por frecuencia:
- WEEKLY -> 7
- 2_WEEKS -> 14
- 3_WEEKS -> 21
- 4_WEEKS -> 28
8. Inserta `RouteDayClient` secuencialmente (`order` incremental).
9. Optimiza orden con Google (`optimize_route_day_with_google`).
10. Crea/actualiza `CollectionRequest` por cada parada.

## Optimizacion Google

Funcion:
- `apps/route/utils.py` -> `optimize_route_day_with_google(route_day)`

Comportamiento:
1. Toma clientes del dia ordenados por `order`.
2. Busca origen en `CompanyHub.location` de la empresa.
3. Elige destino provisional como cliente mas lejano al hub.
4. Envia `origin`, `destination` y `waypoints optimize:true` a Google Directions.
5. Reescribe `RouteDayClient.order` con el orden optimizado.

Fallback seguro:
- si no hay hub
- si no hay `GOOGLE_MAPS_API_KEY`
- si Google responde error/sin rutas

En todos esos casos: se conserva orden existente y el flujo continua.

## CollectionRequest y Celery

Funcion clave:
- `apps/route/utils.py` -> `_schedule_collection_request(route_day_client, route_day_start)`

Reglas:
- `expires_at = route_day_start - 36 horas`
- crea o actualiza `CollectionRequest` (1:1 con parada)
- dedupe/reprogramacion por `auto_estimate_task_id`
- revoca task anterior si cambia programacion

Programacion task:
- `_enqueue_auto_estimate_task(...)`
- si `expires_at <= now`: lanza inmediata
- si no: `apply_async(eta=expires_at)`

Notificacion:
- al crear solicitud nueva se encola `notify_collection_request_created`.

## Uso posterior por cliente/operacion

Endpoints en `CollectionViewSet`:
- `GET /collections/requests/me`
- `GET /collections/requests/{id}`
- `POST /collections/requests/{id}/answer`
- `POST /collections/requests/{id}/manual`

Estados esperados:
- `PENDING`
- `AUTO_ESTIMATED`
- `ANSWERED`
- `MANUAL`

Trazabilidad guardada:
- `answered_by`, `answered_at`
- `manual_by`, `manual_at`
- `auto_estimate_task_id`, `auto_estimate_scheduled_at`

## Filtros en rutas

`RouteFilter` actual:
- `date` -> `route_days__date` (exact)
- `status` -> `route_days__status` (icontains)
- `search` -> `name`, `company__name`, `workers__name`, `workers__surname`

## Resumen rapido

- La generacion semanal esta separada y limpia (viewset -> serializer -> utils).
- Hay control de permisos por empresa para generar.
- Hay dedupe semanal de clientes para no duplicar paradas.
- Se usa Google Directions para optimizar orden.
- Si Google no esta disponible, el proceso no se rompe.
- `CollectionRequest` y tareas Celery quedan enlazadas automaticamente tras generar.

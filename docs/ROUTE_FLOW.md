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

## Ejecucion operativa de ruta diaria

Endpoints nuevos para operar una `RouteDay` ya generada:

- `POST /routes/{id}/route-days/{route_day_id}/start/`
- `POST /routes/{id}/route-days/{route_day_id}/finish/`
- `POST /routes/{id}/route-days/{route_day_id}/stops/{route_day_client_id}/complete/`
- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

Reglas:

- `start`: solo desde `PLANNED` o `PARTIAL` (pasa a `IN_PROGRESS`, set `started_at`).
- `complete`: solo con ruta diaria `IN_PROGRESS`.
- `complete`: bloquea salto de orden por defecto; se puede forzar con `force=true`.
- `complete`: crea `Collection` ligada a `route_day_client` y actualiza `CollectionRequest` a `MANUAL`.
- `finish`: solo desde `IN_PROGRESS` y calcula estado final (`COMPLETED`, `PARTIAL` o `CANCELED`).
- `google-navigation`: devuelve URL de Google Maps con origen hub + waypoints ordenados.

### UX frontend

`Detalle de ruta`:
- Consulta de planificacion semanal.
- Resumen operativo superior.
- Filtro por estado de `RouteDay`.
- Tabla/listado de paradas por dia en modo lectura.
- Acciones principales reducidas a consulta, edicion, generacion y acceso a `Realizar ruta`.

`Realizar ruta`:
- Pantalla separada para operativa diaria (`/routes/:id/execute`).
- Mapa operativo reactivo por dia con hub, secuencia de paradas y acceso directo a Google Maps.
- Acciones de inicio, cierre y registro de paradas integradas en el panel lateral del mapa.
- Seleccion de parada activa sin listado largo duplicado debajo.
- Layout responsive: el panel operativo se apila bajo el mapa hasta resoluciones muy anchas.

`Dashboard`:
- Bloque `Rutas Operativas` con acceso directo a `Realizar ruta` y `Ver detalle`.
- Prioriza visualmente las rutas que encajan con el dia actual.

Notas:
- Accion masiva para expandir/ocultar todos los dias visibles.
- Barra de progreso por dia (registradas vs pendientes).
- En movil, la tabla de paradas se reemplaza por tarjetas por parada para evitar scroll horizontal.

Validaciones de entrada:
- `week_start_date` obligatorio
- `daily_capacity_liters` global **o** `days[]` por fecha
- no se permiten ambos a la vez
- no se permiten fechas duplicadas en `days`
- fechas de `days` deben estar en la semana (`start + 6`)

Permisos:
- `IsOwnerUser` para `generate_week` y `generate_range_routes`
- `IsRouteCompanyGenerator` para consulta operativa y ejecucion de `RouteDay`

## Flujo interno principal

Funcion orquestadora:
- `apps/route/utils.py` -> `generate_week_for_route(route, week_start_date, regenerate=False, daily_capacity_liters=None, days=None)`

Pasos:
1. Crea lock temporal por ruta+semana (`cache.add`) para evitar doble generacion concurrente.
2. Bloquea la ruta en DB con `select_for_update`.
3. Valida rango de fechas contra `route.start_date` y `route.end_date`.
4. Si `regenerate=true`, valida antes que no exista ningun `RouteDay` de la semana con ejecucion previa o recogidas asociadas.
5. Recorre 7 dias de la semana solicitada.
6. Omite dias fuera del rango de la ruta y fuera de `week_start/week_end` de la propia ruta.
7. Crea o recupera `RouteDay` (`get_or_create`).
8. Si un `RouteDay` existente ya no es editable, lo preserva y no modifica paradas ni capacidad.
9. Asigna `daily_capacity_liters` (global o por dia) solo en dias editables.
10. Llama a `generate_route_day_clients(...)` para generar y ordenar paradas.
11. Devuelve lista de `RouteDay` generados/preservados.
12. Libera lock.

## Generacion de paradas (RouteDayClient)

Funcion:
- `apps/route/utils.py` -> `generate_route_day_clients(route_day, regenerate=False, reserved_client_ids=None)`

Pasos:
1. Busca configuracion de zonas de ese weekday (`RouteZoneDay`).
2. Si el `RouteDay` ya no es editable, no modifica nada; y si ademas `regenerate=True`, lanza error.
3. Si `regenerate=True`:
- revoca tareas de `CollectionRequest` existentes
- borra paradas anteriores del dia
4. Si hay `reserved_client_ids` (clientes ya planificados en la semana), elimina duplicados existentes de ese dia.
5. Construye filtro espacial OR con `location__within` para todas las zonas del dia.
6. Busca clientes de la empresa con geolocalizacion.
7. Anota `last_collection_date` por cliente para evitar N+1.
7.1. Esa ultima recogida y la ultima planificacion previa se calculan dentro de la misma empresa de la ruta, para no mezclar historico si un cliente pertenece a varias empresas.
8. Filtra clientes "due" por frecuencia:
- WEEKLY -> 7
- 2_WEEKS -> 14
- 3_WEEKS -> 21
- 4_WEEKS -> 28
9. Inserta `RouteDayClient` secuencialmente (`order` incremental) respetando:
- `max_clients_per_day`
- `daily_capacity_liters` de forma estricta desde la primera parada
10. Optimiza orden con Google (`optimize_route_day_with_google`).
11. Crea/actualiza `CollectionRequest` por cada parada.

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
- `generate-week` solo lo puede ejecutar owner.
- Hay dedupe semanal de clientes para no duplicar paradas.
- Los dias ya operados no se tocan en regeneraciones normales y bloquean `regenerate=true`.
- Se usa Google Directions para optimizar orden.
- Si Google no esta disponible, el proceso no se rompe.
- `CollectionRequest` y tareas Celery quedan enlazadas automaticamente tras generar.

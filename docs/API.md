# API GreenPath (Backend Django)

## 1. Informacion general

- Base path API: `/`
- Documentacion OpenAPI: `GET /schema/`
- Swagger UI: `GET /docs/`
- Admin Django: `GET /admin/`
- Auth principal: JWT Bearer (header `Authorization: Bearer <access_token>`)
- Timezone en backend: `UTC` (`USE_TZ=True`)
- Paginacion por defecto: `page_size=10` (parametro `page_size` soportado)

## 2. Autenticacion

### `POST /login/`
Login con usuario y password.

Request:
```json
{
  "username": "owner1",
  "password": "secret"
}
```

Response 200:
```json
{
  "token": "<access>",
  "refresh-token": "<refresh>",
  "user": {
    "username": "owner1",
    "email": "owner@example.com",
    "role_type": "Propietario"
  },
  "message": "Login successfully"
}
```

### `POST /authenticate/login`
Login con Google ID token.

Request:
```json
{
  "credential": "<google_id_token>"
}
```

Response 200:
```json
{
  "t": "<access>",
  "refresh-token": "<refresh>",
  "user": {
    "id": 1,
    "username": "owner1",
    "email": "owner@example.com",
    "role_type": "Propietario"
  }
}
```

### `POST /token/refresh/`
Renueva access token (SimpleJWT).

### `POST /logout/`
Cierre de sesion logico.

Request:
```json
{
  "user": 1
}
```

## 3. Roles y permisos (resumen)

- `owner`: rol principal de gestion.
- `worker`: operacion de empresa.
- `client`: portal cliente.
- `staff/superuser`: acceso administrativo ampliado.

Notas:
- Hay restricciones por rol y tambien por empresa en varios `get_queryset`.
- Algunas validaciones de permisos se refuerzan dentro de acciones custom (ejemplo: collection requests).

## 4. Convenciones de respuesta

- Exito tipico: `200/201` con objeto o `results`.
- Error validacion: `400`.
- No autorizado/autenticacion: `401`.
- Prohibido por rol/empresa: `403`.
- No encontrado: `404`.
- Conflicto (lock de generacion semanal): `409`.

Paginacion:
- Formato A (paginador global): `count`, `total_pages`, `next`, `previous`, `results`.
- Formato B (algunos list custom): `count`, `next`, `previous`, `results` (sin `total_pages`).

## 5. Endpoints por modulo

### 5.1 Users (`/users/`)

CRUD base (`GET/POST /users/`, `GET/PUT/PATCH/DELETE /users/{id}/`).

Actions:
- `POST /users/set_password/`
- `GET /users/profile/`
- `PUT /users/profile/`

Filtros soportados:
- `username`, `email`, `is_active`, `is_superuser`, `is_staff`

### 5.2 Workers (`/workers/`)

CRUD base (`GET/POST /workers/`, `GET/PUT/PATCH/DELETE /workers/{id}/`).

Actions:
- `PUT /workers/{id}/activate/`

Filtros soportados:
- `name`, `surname`, `phone`, `dni`, `role`, `disabled`, `search`

### 5.3 Clients (`/clients/`)

CRUD base (`GET/POST /clients/`, `GET/PUT/PATCH/DELETE /clients/{id}/`).

Actions:
- `GET /clients/historial/{client_id}/`

Filtros soportados:
- `name`, `phone`, `cif`, `address`, `frequency`, `search`

### 5.4 Companies (`/companies/`)

CRUD base (`GET/POST /companies/`, `GET/PUT/PATCH/DELETE /companies/{id}/`).

Filtros soportados:
- `name`, `address`, `phone`, `email`, `cif`

### 5.5 Zones (`/zones/`)

CRUD base (`GET/POST /zones/`, `GET/PUT/PATCH/DELETE /zones/{id}/`).

Filtros/busqueda:
- Filtro: `name`
- Search: `search` (sobre `name`)

Payload zona (create/update):
- `name`
- `polygon` en WKT (`POLYGON((lng lat,...))`) o array `[[lng,lat], ...]`

### 5.6 Trucks (`/trucks/`)

CRUD base (`GET/POST /trucks/`, `GET/PUT/PATCH/DELETE /trucks/{id}/`).

Action:
- `POST /trucks/assign-driver/{worker_id}/`

Request assign driver:
```json
{
  "truck_id": 10,
  "force": false
}
```

Filtros soportados:
- `registration_number`, `brand`, `model`, `status`, `fuel`
- `year`, `year_gte`, `year_lte`
- `company`, `driver`, `search`

### 5.7 Routes (`/routes/`)

CRUD base (`GET/POST /routes/`, `GET/PUT/PATCH/DELETE /routes/{id}/`).

Actions:
- `POST /routes/{id}/generate-range-routes/`
- `POST /routes/{id}/generate-week/`
- `GET /routes/{id}/operational-overview/`
- `POST /routes/{id}/route-days/{route_day_id}/start/`
- `POST /routes/{id}/route-days/{route_day_id}/finish/`
- `POST /routes/{id}/route-days/{route_day_id}/stops/{route_day_client_id}/complete/`
- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

Filtros soportados:
- `date`, `status`
- `search`

`GET /routes/{id}/operational-overview/`:
- query param opcional `week_start_date=YYYY-MM-DD` para cargar una semana concreta.
- devuelve `route.hub` con `id`, `name` y `location {lat, lng}` si la empresa tiene hub geolocalizado.
- devuelve `client_location {lat, lng}` en cada parada para pintar el mapa operativo del frontend.

#### `POST /routes/{id}/generate-week/`
Genera/actualiza los `RouteDay` de una semana y sus paradas (`RouteDayClient`), optimiza orden con Google Directions y crea/programa `CollectionRequest`.

Reglas:
- Idempotente.
- Dos modos de capacidad:
  - Global: `daily_capacity_liters`
  - Por dia: `days[]` con `date` + `daily_capacity_liters`
- `regenerate=true` solo se permite si todos los `RouteDay` de la semana siguen siendo editables, sin ejecucion previa ni recogidas asociadas.
- Si la semana contiene dias no editables o con trazabilidad operativa previa, devuelve `400`.
- Si `regenerate=false`, los `RouteDay` ya operados se preservan y no se modifican.
- La capacidad diaria se respeta de forma estricta: no se crea una parada si hace que el total planificado supere `daily_capacity_liters`.
- Si ya existe una generacion en curso para misma ruta+semana, devuelve `409`.

Request modo A:
```json
{
  "week_start_date": "2026-02-23",
  "regenerate": true,
  "daily_capacity_liters": "1800.00"
}
```

Request modo B:
```json
{
  "week_start_date": "2026-02-23",
  "regenerate": false,
  "days": [
    {"date": "2026-02-23", "daily_capacity_liters": "1500.00"},
    {"date": "2026-02-25", "daily_capacity_liters": "1700.00"}
  ]
}
```

Response 200:
```json
{
  "message": "Ruta operativa semanal generada correctamente",
  "route_days": [
    {"id": 101, "date": "2026-02-23", "daily_capacity_liters": "1500.00", "stops": 12}
  ]
}
```

Validaciones comunes:
- Debe venir `daily_capacity_liters` o `days`.
- No pueden venir ambos a la vez.
- En `days`, fechas duplicadas no permitidas.
- En `days`, todas las fechas deben estar dentro de la semana (`week_start_date` a `+6 dias`).
- La semana debe estar dentro del rango de la ruta.
- No se puede regenerar una semana con dias ya iniciados, parciales o completados.

#### `POST /routes/{id}/generate-range-routes/`
Endpoint legacy para generar rutas en rango de fechas por configuracion de zonas.

Request:
```json
{
  "start_date": "2026-02-23",
  "end_date": "2026-02-28",
  "zone_schedule": {
    "0": ["Zona Norte"],
    "2": ["Zona Centro", "Zona Este"]
  },
  "max_clients": 25
}
```

### 5.8 Collections (`/collections/`)

CRUD base (`GET/POST /collections/`, `GET/PUT/PATCH/DELETE /collections/{id}/`).

Filtros soportados:
- `client` (nombre cliente)
- `worker` (nombre worker)
- `status`
- `worker_id`

Actions nuevas de planificacion:
- `GET /collections/requests/me/`
- `GET /collections/requests/{request_id}/`
- `POST /collections/requests/{request_id}/answer/`
- `POST /collections/requests/{request_id}/manual/`

#### `GET /collections/requests/me/`
Listado de solicitudes del cliente autenticado.

Query params:
- `status` opcional (`PENDING`, `AUTO_ESTIMATED`, `ANSWERED`, `MANUAL`)

Si no envias `status`, por defecto lista `PENDING` + `AUTO_ESTIMATED`.

#### `GET /collections/requests/{request_id}/`
Detalle de solicitud.

Acceso:
- Cliente propietario de la solicitud.
- Owner/Worker de la misma empresa de la ruta.

#### `POST /collections/requests/{request_id}/answer/`
Respuesta del cliente con litros finales.

Request:
```json
{
  "final_liters": "240.50"
}
```

Reglas:
- Solo cliente propietario.
- Estado permitido: `PENDING` o `AUTO_ESTIMATED`.
- Debe no estar expirada (`timezone.now() < expires_at`).

Efectos:
- `final_source=CLIENT`
- `status=ANSWERED`
- guarda trazabilidad `answered_by`, `answered_at`

#### `POST /collections/requests/{request_id}/manual/`
Carga manual por owner/worker de la empresa.

Request:
```json
{
  "final_liters": "230.00"
}
```

Efectos:
- `final_source=MANUAL`
- `status=MANUAL`
- guarda trazabilidad `manual_by`, `manual_at`

## 6. Flujo de planificacion semanal (operativo)

1. `generate-week` crea/actualiza `RouteDay` para los dias habilitados de la ruta.
2. Si `regenerate=false`, preserva cualquier `RouteDay` que ya no sea editable.
3. Si `regenerate=true`, valida antes que toda la semana sea editable y aborta completa si no lo es.
4. Para cada dia editable, busca `RouteZoneDay` por `weekday`.
5. Selecciona clientes por geofiltro (`location__within` de los poligonos de zona) y por frecuencia/vencimiento de recogida.
6. Inserta `RouteDayClient` con orden secuencial inicial sin sobrepasar `max_clients_per_day` ni `daily_capacity_liters`.
7. Optimiza orden con Google Directions:
- origen: `CompanyHub.location`
- waypoints: clientes
- sin retornos al hub en esta fase
8. Reescribe `order` en `RouteDayClient`.
9. Crea/actualiza `CollectionRequest` por parada:
- `expires_at = inicio_route_day - 36 horas`
- programa tarea Celery `auto_estimate_collection_request_liters` con `eta=expires_at`
- si `expires_at <= now`, se encola inmediata
- se encola email `notify_collection_request_created`

## 7. Modelo CollectionRequest (campos relevantes)

- `route_day_client` (one-to-one)
- `expires_at`
- `status`: `PENDING`, `ANSWERED`, `AUTO_ESTIMATED`, `MANUAL`
- `container_type`, `container_number`
- `estimated_liters`, `final_liters`, `final_source`
- Trazabilidad:
- `answered_by`, `answered_at`
- `manual_by`, `manual_at`
- Scheduling task:
- `auto_estimate_task_id`, `auto_estimate_scheduled_at`

## 8. Valores enumerados importantes

- `PickupFrequency`: `WEEKLY`, `2_WEEKS`, `3_WEEKS`, `4_WEEKS`
- `RouteDayStatus`: `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `PARTIAL`, `CANCELED`
- `CollectionRequestStatus`: `PENDING`, `ANSWERED`, `AUTO_ESTIMATED`, `MANUAL`
- `PlannedSource`: `CLIENT`, `AUTO`, `MANUAL`
- `ContainerType`: `BIDONES`, `IBC`

## 9. Ejemplos rapidos (curl)

### Login
```bash
curl -X POST http://localhost:8000/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"owner1","password":"secret"}'
```

### Generate week
```bash
curl -X POST http://localhost:8000/routes/12/generate-week/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"week_start_date":"2026-02-23","regenerate":true,"daily_capacity_liters":"1800.00"}'
```

### Cliente responde litros
```bash
curl -X POST http://localhost:8000/collections/requests/55/answer/ \
  -H "Authorization: Bearer <token_cliente>" \
  -H "Content-Type: application/json" \
  -d '{"final_liters":"245.00"}'
```

### Worker/Owner carga manual
```bash
curl -X POST http://localhost:8000/collections/requests/55/manual/ \
  -H "Authorization: Bearer <token_owner_o_worker>" \
  -H "Content-Type: application/json" \
  -d '{"final_liters":"240.00"}'
```

## 10. Recomendacion de uso

- Para contrato exacto de schemas, usa siempre `GET /schema/` o `GET /docs/`.
- Esta guia sirve como referencia funcional y de negocio de la API real del proyecto.

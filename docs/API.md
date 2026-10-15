# API GreenPath (Backend Django)

Fecha de revision: 2026-10-09

## 1. Objetivo de este documento

Este documento describe los contratos principales de la API backend de GreenPath.
Su funcion es servir como referencia para:

- desarrollo frontend
- pruebas manuales o automatizadas
- integraciones futuras
- revisiones funcionales y tecnicas

El documento se centra en:

- endpoints disponibles
- permisos de acceso
- payloads esperados
- convenciones de respuesta
- reglas de negocio visibles desde la API

Aunque se trata de un documento tecnico, conviene recordar que la API de GreenPath no es solo un canal de CRUD. Es una pieza estructural del TFG porque concentra una parte importante de la logica funcional del sistema:

- aislamiento por empresa
- permisos por rol
- validacion de reglas de negocio
- calculo economico sensible
- acciones operativas complejas como `generate-week`, ejecucion diaria o cierre de recogidas
- exposicion de datos enriquecidos al frontend

Desde la perspectiva academica, esto aporta valor porque demuestra una separacion clara entre capa de presentacion y capa de negocio, y porque la API actua como contrato real entre modulos.

Para contexto de producto y negocio conviene complementar esta lectura con:

- `docs/FUNCIONAL.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/ROUTE_FLOW.md`

## 2. Informacion general

- Base path API: `/`
- Documentacion OpenAPI: `GET /schema/`
- Swagger UI: `GET /docs/`
- Admin Django: `GET /admin/`
- Auth principal: JWT Bearer (header `Authorization: Bearer <access_token>`)
- Timezone en backend: `UTC` (`USE_TZ=True`)
- Paginacion por defecto: `page_size=10` (parametro `page_size` soportado)

## 3. Modelo de acceso

Roles principales:

- `owner`: gestion completa
- `worker`: operacion de empresa
- `client`: portal cliente
- `staff/superuser`: administracion ampliada

Notas:

- La mayoria de consultas y acciones se restringen por rol y por empresa.
- Algunos permisos se refuerzan en acciones custom, incluso si el `get_queryset` ya reduce el alcance.
- El bloque economico (`buyers`, `sales`, configuracion fiscal) esta reservado a `owner`.

## 3.1 Valor arquitectonico de la API propia

La API tiene varias funciones de alto valor dentro del sistema:

- centraliza la verdad funcional del negocio
- evita que el frontend pueda imponer calculos sensibles
- mantiene consistencia entre experiencia web, tareas asincronas y persistencia
- permite documentar y testear el comportamiento del producto de forma verificable

Esta aproximacion es especialmente importante en GreenPath porque la aplicacion mezcla:

- rutas y geografia
- solicitudes y recogidas
- configuracion fiscal
- ventas y documentos PDF
- acciones asincronas

Una logica tan variada no deberia repartirse de forma arbitraria entre frontend y backend. Por eso, la API de GreenPath no es un accesorio de transporte de datos, sino una capa de aplicacion con peso propio.

## 3.2 Relacion entre API e integraciones del proyecto

La API es tambien el punto donde se materializa gran parte del valor de las integraciones consumidas por GreenPath. No todas aparecen como endpoints externos dedicados, pero si atraviesan el comportamiento funcional de varias acciones:

- la creacion y edicion de clientes puede disparar geocodificacion basada en Google Maps
- `generate-week` puede usar Google Directions para ordenar paradas
- la ejecucion de rutas consume datos compatibles con navegacion externa y mapas de Leaflet
- la creacion de solicitudes de recogida puede programar tareas diferidas en Celery
- la notificacion al cliente y el correo de acceso utilizan Gmail API
- la descarga de facturas de venta activa el renderizado PDF con WeasyPrint

Desde el punto de vista del contrato API, esto significa que algunos endpoints no solo crean o actualizan modelos, sino que orquestan procesos mas amplios:

- persistencia
- validacion
- enriquecimiento de respuesta
- coordinacion asincrona
- integracion documental

## 4. Convenciones de respuesta

Codigos tipicos:

- `200`: lectura o accion correcta
- `201`: recurso creado
- `204`: sin contenido
- `400`: error de validacion o regla de negocio
- `401`: autenticacion ausente o invalida
- `403`: acceso denegado por rol o empresa
- `404`: recurso no encontrado
- `409`: conflicto, por ejemplo lock funcional de generacion semanal

Paginacion:

- Formato A: `count`, `total_pages`, `next`, `previous`, `results`
- Formato B: `count`, `next`, `previous`, `results`

Convenciones practicas:

- Algunos serializers exponen campos enriquecidos para frontend como `*_label`, `*_name` o datos agregados.
- Cuando existe logica economica, backend recalcula los importes relevantes y no se fia del frontend como fuente final de verdad.
- Las respuestas de acciones custom suelen incluir `message` y, cuando aplica, el recurso o resumen afectado.
- En modulos con complejidad operativa, la API devuelve contexto enriquecido para reducir logica de negocio en cliente.

## 4.1 Enriquecimiento de respuestas y por que importa

La API no devuelve unicamente campos brutos de base de datos. En muchos endpoints se incorporan:

- etiquetas legibles para enums
- nombres de entidades relacionadas
- agregados economicos
- campos calculados de apoyo a la interfaz
- bloques operativos como `operational_plan`

Esto tiene varias ventajas:

- simplifica el frontend
- reduce duplicacion de reglas
- mantiene coherencia entre listados, detalles y estadisticas
- facilita testing y depuracion del sistema

## 5. Autenticacion

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

Comportamiento:
- si las credenciales son correctas, el backend actualiza `User.last_login`
- si las credenciales fallan, no se modifica `last_login`

### `POST /authenticate/login`
Login con Google ID token.

El backend acepta el token en `credential` o en `token`. El frontend actual usa `token` y puede enviar metadatos adicionales no obligatorios para el backend, como `email`, `lang` o `signature`.

Request:
```json
{
  "token": "<google_id_token>",
  "email": "owner@example.com",
  "lang": "es",
  "signature": "<firma_frontend>"
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

Nota:
- el frontend actual cierra sesion limpiando tokens locales y redirigiendo a `/socialLogin`; este endpoint queda disponible para integraciones o evolucion posterior del cierre de sesion servidor.

## 6. Endpoints por modulo

### 6.1 Users (`/users/`)

CRUD base (`GET/POST /users/`, `GET/PUT/PATCH/DELETE /users/{id}/`).

Actions:
- `POST /users/set_password/`
- `GET /users/profile/`
- `PUT /users/profile/`

Perfil:
- `PUT /users/profile/` permite actualizar `email`, `name`, `phone` y `photo`
- para subir `photo` se debe usar `multipart/form-data`
- la foto se guarda en el perfil asociado (`Worker` para owner/worker, `Client` para client)
- la respuesta de `GET /users/profile/` devuelve el bloque `profile` enriquecido con los campos visibles del rol

Filtros soportados:
- `username`, `email`, `is_active`, `is_superuser`, `is_staff`

### 6.2 Workers (`/workers/`)

CRUD base (`GET/POST /workers/`, `GET/PUT/PATCH/DELETE /workers/{id}/`).

Actions:
- `PUT /workers/{id}/activate/`

Filtros soportados:
- `name`, `surname`, `phone`, `dni`, `role`, `disabled`, `search`

Reglas relevantes:
- `POST /workers/` crea siempre trabajadores operativos normales con `role=worker`
- el flujo API usado por frontend no debe utilizarse para crear `owner`
- `PUT/PATCH /workers/{id}/` no se considera via valida para cambiar `role` o `company`

### 6.3 Clients (`/clients/`)

CRUD base (`GET/POST /clients/`, `GET/PUT/PATCH/DELETE /clients/{id}/`).

Actions:
- `GET /clients/historial/{client_id}/`

Filtros soportados:
- `name`, `phone`, `cif`, `address`, `frequency`, `search`

Reglas relevantes:
- `cif` es opcional y admite cadena vacia
- en alta, `user.username` y `user.email` son opcionales si `get_access=false`
- si `get_access=true`, el email es obligatorio para enviar acceso a la plataforma
- cuando faltan `username` o `email`, el backend genera credenciales internas a partir del nombre

### 6.4 Companies (`/companies/`)

CRUD base (`GET/POST /companies/`, `GET/PUT/PATCH/DELETE /companies/{id}/`).

Filtros soportados:
- `name`, `address`, `phone`, `email`, `cif`

Actions:
- `GET /companies/settings/`
- `PUT /companies/settings/`

#### `GET /companies/settings/`

Devuelve la configuracion global de la empresa asociada al usuario autenticado.

Acceso:
- `owner`: si
- `worker`: si, solo lectura
- `client`: no

#### `PUT /companies/settings/`

Actualiza la configuracion global de la empresa del owner autenticado.

Payload actual:

```json
{
  "default_price_per_liter": "1.250",
  "billing_business_name": "Servicios Coria S.L.",
  "billing_tax_id": "B12345678",
  "billing_address": "Poligono Industrial La Estrella, Nave 12",
  "billing_postal_code": "41110",
  "billing_city": "Bollullos de la Mitacion",
  "billing_province": "Sevilla",
  "billing_country": "Espana",
  "billing_phone": "955123456",
  "billing_email": "facturacion@servicioscoria.es",
  "billing_bank_account": "ES7620770024003102575766",
  "billing_ler_code": "20 01 25",
  "billing_footer": "Factura generada desde GreenPath.",
  "collections_enabled": true,
  "bulk_collections_enabled": true,
  "oil_density_kg_per_liter": "0.9200",
  "hub_name": "Nave Principal Coria",
  "hub_lat": 37.453664,
  "hub_lng": -5.973891
}
```

Uso actual:
- precio por litro por defecto para recogidas manuales
- precio por litro por defecto para recogidas creadas desde ejecucion de ruta
- datos fiscales y bancarios usados como plantilla para nuevas facturas de venta
- configuracion del hub para operativa de rutas
- consulta del estado de los modulos de recogidas y recogidas al por mayor

`GET /companies/features/` devuelve solo los indicadores de modulos de la empresa del usuario. El frontend usa este endpoint para ocultar las secciones desactivadas y el backend tambien bloquea sus endpoints.

`collections_enabled` y `bulk_collections_enabled` son campos de solo lectura en la API. Su activacion se gestiona exclusivamente desde Django Admin.

Nota:
- el modelo conserva `billing_logo` para facturacion, aunque el endpoint actual de settings no lo expone en el payload principal
- al crear una venta, el backend congela esos datos en `SaleInvoiceIssuerSnapshot`; cambiar `CompanySettings` despues no altera facturas antiguas

### 6.5 Zones (`/zones/`)

CRUD base (`GET/POST /zones/`, `GET/PUT/PATCH/DELETE /zones/{id}/`).

Filtros/busqueda:
- Filtro: `name`
- Search: `search` (sobre `name`)

Payload zona (create/update):
- `name`
- `polygon` en WKT (`POLYGON((lng lat,...))`) o array `[[lng,lat], ...]`

### 6.6 Trucks (`/trucks/`)

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

### 6.7 Routes (`/routes/`)

CRUD base (`GET/POST /routes/`, `GET/PUT/PATCH/DELETE /routes/{id}/`).

Actions:
- `POST /routes/{id}/generate-week/`
- `GET /routes/{id}/zone-config/`
- `PUT /routes/{id}/zone-config/`
- `GET /routes/{id}/operational-overview/`
- `POST /routes/{id}/route-days/{route_day_id}/start/`
- `POST /routes/{id}/route-days/{route_day_id}/finish/`
- `POST /routes/{id}/route-days/{route_day_id}/stops/{route_day_client_id}/complete/`
- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

Filtros soportados:
- `date`, `status`
- `search`

Acceso:
- `create`, `update`, `destroy`, `zone-config` y `generate-week`: `owner`
- lectura, detalle operativo y acciones de ejecucion diaria: `owner` de la empresa o `worker` asignado a la ruta

`GET /routes/{id}/operational-overview/`:
- query param opcional `week_start_date=YYYY-MM-DD` para cargar una semana concreta.
- devuelve `route.hub` con `id`, `name` y `location {lat, lng}` si la empresa tiene hub geolocalizado.
- devuelve `client_location {lat, lng}` en cada parada para pintar el mapa operativo del frontend.
- devuelve `operational_plan` por cada `RouteDay` con:
  - `capacity_liters`
  - `planned_load_liters`
  - `registered_load_liters`
  - `segments_count`
  - `returns_to_hub_count`
  - `requires_hub_return`
  - `active_segment_number`
  - `active_segment_route_day_client_id`
  - `active_segment_current_load_liters`
  - `active_segment_remaining_capacity_liters`
  - `segments[]`
- estos campos sirven de soporte para mapa, sugerencia de siguiente parada y navegacion; la UI actual no expone literalmente tarjetas tecnicas de `tramo` al usuario

#### `GET /routes/{id}/zone-config/`

Devuelve la configuracion de zonas por dia de la semana asociada a la ruta.

Response 200:
```json
{
  "zone_days": [
    {
      "weekday": 0,
      "zones": [
        {"id": 4, "name": "Coria del Rio"}
      ]
    }
  ]
}
```

#### `PUT /routes/{id}/zone-config/`

Reemplaza la configuracion de zonas por weekday de la ruta. Si un weekday no aparece en `zone_days`, su configuracion anterior se elimina.

Request:
```json
{
  "zone_days": [
    {"weekday": 0, "zones": [4, 7]},
    {"weekday": 2, "zones": [5]}
  ]
}
```

Reglas:
- `weekday` usa valores `0..6` (`0` lunes, `6` domingo).
- no se permiten weekdays duplicados.
- `zones` es una lista de ids de zonas existentes.
- el frontend actual guarda esta configuracion despues de crear o editar la ruta.

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
- La capacidad determina segmentos y retornos al hub, no un tope de litros para seleccionar clientes. La seleccion se limita por frecuencia, zonas, reservas semanales y `max_clients_per_day`.
- el criterio funcional actual aplica tambien un maximo por defecto de `10` clientes por jornada.
- Si ya existe una generacion en curso para misma ruta+semana, devuelve `409`.

Campos de payload:
- `week_start_date`: obligatorio, formato `YYYY-MM-DD`.
- `regenerate`: opcional, por defecto `false`.
- `auto_estimate_without_contact`: opcional, por defecto `false`; el frontend actual lo expone como `Autoestimar sin notificar al cliente`.
- `daily_capacity_liters`: capacidad global para los dias generados.
- `days`: alternativa a `daily_capacity_liters` para definir capacidad por fecha.
- `max_clients_per_day`: opcional, minimo `1`, maximo `100`, por defecto `10`; el frontend actual no lo expone y deja que backend aplique el valor por defecto.

Request modo A:
```json
{
  "week_start_date": "2026-02-23",
  "regenerate": true,
  "daily_capacity_liters": "1800.00",
  "auto_estimate_without_contact": false
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
  ],
  "max_clients_per_day": 10
}
```

Response 200:
```json
{
  "message": "Ruta operativa semanal generada correctamente",
  "route_days": [
    {
      "id": 101,
      "date": "2026-02-23",
      "daily_capacity_liters": "1500.00",
      "stops": 10,
      "optimization_status": "OPTIMIZED",
      "optimization_message": "<mensaje del resultado>",
      "optimized_at": "2026-02-20T10:00:00Z"
    }
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

#### `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

Devuelve enlaces de navegacion externa a Google Maps para una jornada.

Response 200:
```json
{
  "url": "https://www.google.com/maps/dir/?api=1&...",
  "urls": [
    "https://www.google.com/maps/dir/?api=1&..."
  ],
  "is_split": false
}
```

Reglas:
- `url` mantiene compatibilidad con clientes antiguos y contiene el primer enlace.
- `urls` contiene todos los enlaces cuando la jornada se parte por limite practico de waypoints.
- la navegacion sale del hub, respeta retornos al hub por capacidad y vuelve al hub al cierre del tramo.
- las paradas sin ubicacion no se incluyen en el enlace de navegacion.

### 6.8 Collections (`/collections/`)

CRUD base (`GET/POST /collections/`, `GET/PUT/PATCH/DELETE /collections/{id}/`).

Filtros soportados:
- `client` (nombre cliente)
- `worker` (nombre worker)
- `status`
- `worker_id`
- `billable`
- `start_date`
- `end_date`
- `search` (worker y fecha para client; worker, cliente, CIF, notas, estado y ruta para owner/worker)

Notas de negocio:
- si no se envia `price_per_liter` al crear una recogida manual, se usa `CompanySettings.default_price_per_liter`
- al registrar una parada desde una ruta, la recogida nace con el precio global de la empresa
- `deduction_reason_label` expone el valor traducido del enum para detalle frontend

Notas:
- `billable` es opcional y por defecto vale `true`
- `billable_label` expone `Facturable` o `No facturable`
- si `billable=false`, la recogida sigue siendo operativa y visible, pero queda fuera de estadisticas economicas, `total_paid` de cliente y `total_incomes` de trabajador

Actions de solicitudes:
- `GET /collections/requests/me/`
- `GET /collections/requests/{request_id}/`
- `POST /collections/requests/{request_id}/answer/`
- `POST /collections/requests/{request_id}/manual/`

#### `GET /collections/requests/me/`
Listado de solicitudes del cliente autenticado.

Query params:
- `status` opcional (`ALL`, `PENDING`, `AUTO_ESTIMATED`, `ANSWERED`, `MANUAL`)

Reglas:
- si no envias `status` o envias `ALL`, devuelve todos los estados visibles del cliente
- ordena por `created_date` descendente y despues por `id` descendente
- endpoint solo para rol `client`

#### `GET /collections/requests/{request_id}/`
Detalle de solicitud.

Acceso:
- Cliente propietario de la solicitud.
- Owner/Worker de la misma empresa de la ruta.

#### `POST /collections/requests/{request_id}/answer/`
Respuesta del cliente por envases. El backend calcula los litros finales.

Request recomendado:
```json
{
  "container_type": "BIDONES",
  "container_number": 3
}
```

Capacidades:
- `BIDONES`: 60 L por unidad
- `IBC`: 1000 L por unidad

Reglas:
- Solo cliente propietario.
- Estado permitido: `PENDING` o `AUTO_ESTIMATED`.
- Debe no estar expirada (`timezone.now() < expires_at`).
- `final_liters` se acepta como compatibilidad legacy, pero el flujo principal usa envases.

Efectos:
- `final_source=CLIENT`
- `status=ANSWERED`
- `final_liters` y `estimated_liters` quedan sincronizados con el calculo resultante
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

### 6.9 Buyers (`/buyers/`)

CRUD base (`GET/POST /buyers/`, `GET/PUT/PATCH/DELETE /buyers/{id}/`).

Acceso:
- solo `owner`

Filtros soportados:
- `fiscal_name`
- `tax_id`
- `city`
- `province`
- `search`

Campos principales:
- `fiscal_name`
- `tax_id`
- `fiscal_address`
- `postal_code`
- `city`
- `province`
- `country`
- `email`
- `phone`
- `contact_person`
- `notes`

Notas:
- Es un modulo interno.
- Los compradores no acceden a la plataforma.
- `full_fiscal_address` se expone en lectura para facilitar detalle y facturacion.

### 6.10 Sales (`/sales/`)

CRUD base (`GET/POST /sales/`, `GET/PUT/PATCH/DELETE /sales/{id}/`).

Acceso:
- solo `owner`

Filtros soportados:
- `invoice_number`
- `buyer`
- `invoice_year`
- `start_date`
- `end_date`
- `search`

Campos de escritura:
- `buyer`
- `invoice_number`
- `invoice_date`
- `currency`
- `notes`
- `lines`: lista no vacia de conceptos, cada uno con:
  - `product_description`
  - `quantity`
  - `unit`
  - `unit_price`
  - `tax_rate`

Reglas:
- `invoice_number` es manual y obligatorio.
- `invoice_date` es la unica fecha visible y funcional del modulo.
- internamente `sale_date` se sincroniza con `invoice_date` para mantener compatibilidad del modelo.
- al crear una venta se vincula un snapshot fiscal del emisor (`SaleInvoiceIssuerSnapshot`) con razon social, CIF, direccion, telefono, email, cuenta bancaria, logo, LER y pie de factura.
- si los datos fiscales actuales coinciden con un snapshot anterior de la misma empresa, se reutiliza; si cambian, se crea uno nuevo para las nuevas facturas.
- cada linea calcula su base, IVA y total. `unit_price` admite hasta ocho decimales (18 digitos en total); `quantity` admite dos. Base, IVA y total se redondean a dos decimales.
- `subtotal`, `tax_amount` y `total` de la venta se obtienen sumando sus lineas.
- los payloads antiguos de un solo concepto siguen siendo compatibles.
- el PDF no se almacena: se genera bajo demanda cuando se descarga, usando la venta, el comprador y el snapshot fiscal asociado.
- `invoice_issuer` es interno y no se expone en el serializer publico de ventas para no cambiar el contrato del frontend.

#### `GET /sales/{id}/invoice/download/`

Descarga el PDF de factura.

Comportamiento:
- backend construye el PDF en memoria en cada solicitud
- los datos fiscales y bancarios del emisor se leen del snapshot asociado a la venta
- no persiste el fichero en almacenamiento
- devuelve un adjunto `application/pdf`

#### `GET /sales/economic-summary/`

Resumen economico global por empresa.

Query params opcionales:

- `start_date=YYYY-MM-DD`
- `end_date=YYYY-MM-DD`

Reglas:

- si envias filtro, debes enviar `start_date` y `end_date` juntos
- ambos rangos se aplican sobre `invoice_date` en ventas y `collection_date` en recogidas
- la serie `monthly` se recalcula solo para los meses incluidos en el rango solicitado

Response 200:
```json
{
  "total_cost": "15420.00",
  "total_income": "74288.38",
  "net_profit": "58868.38",
  "total_bought_volume": "12110.00",
  "total_sold_volume": "61540.00",
  "bought_quantities": {"L": "12110.0000", "KG": "11141.2000"},
  "sold_quantities": {"L": "61540.0000", "KG": "56616.8000"},
  "bulk_collection_cost": "0.00",
  "ignored_quantities": {"bulk_collections": 0, "sales": 0},
  "conversion": {"base_unit": "L", "oil_density_kg_per_liter": "0.9200"},
  "monthly": [
    {
      "year": 2026,
      "month": 3,
      "income": "23568.62",
      "cost": "2140.20",
      "profit": "21428.42",
      "sold_quantities": {"L": "19450.0000", "KG": "17894.0000"},
      "bought_quantities": {"L": "1830.0000", "KG": "1683.6000"},
      "ignored_quantities": {"bulk_collections": 0, "sales": 0}
    }
  ]
}
```

Interpretacion:
- `total_cost`: coste de recogidas (`Collection`) confirmadas y facturables mas recogidas al por mayor facturables
- `total_income`: ingresos de ventas (`Sale`)
- `net_profit`: ingresos menos costes
- `monthly`: serie mensual para panel economico
- `total_bought_volume`: litros medidos de recogidas confirmadas y facturables mas cantidad convertible de recogidas al por mayor (incluye tambien las no facturables)

## 7. Convenciones transversales de la API

### 7.1 Fechas y horas

- los `datetime` se almacenan en backend con `USE_TZ=True`
- el frontend debe tratar las fechas operativas (`date`) como fechas de negocio, no como `datetime`
- en rutas y ventas hay que diferenciar entre fecha funcional y timestamps tecnicos
- `expires_at`, `started_at`, `finished_at` y campos similares deben mostrarse en zona horaria de interfaz

### 7.2 Importes y precision

- los importes monetarios se calculan en backend y viajan como `string` decimal
- el frontend no debe recalcular subtotales o totales como fuente de verdad final
- en recogidas y ventas los campos economicos se deben considerar de precision fija

### 7.3 Coordenadas y GIS

- las zonas pueden enviarse en WKT o como lista de coordenadas `lng/lat`
- la ubicacion de clientes y hubs se trabaja con SRID 4326
- las reglas geograficas de inclusion en ruta dependen de que `location` exista realmente

### 7.4 Paginacion y filtros

- todos los listados deben asumir respuesta paginada salvo indicacion contraria
- cuando un modulo soporte `search`, el frontend debe usarlo como entrada principal de busqueda libre
- filtros booleanos como `billable`, `disabled` o similares deben enviarse como `true/false`

## 8. Errores funcionales frecuentes expuestos por la API

- `400` en `generate-week` por fecha invalida, payload inconsistente o regla de negocio incumplida
- `409` en `generate-week` cuando existe lock funcional o conflicto de regeneracion
- `400` en `collections` si la medicion o las deducciones son inconsistentes
- `400` en `sales` si el numero de factura ya existe para la misma empresa
- `403` cuando un rol intenta acceder a bloques owner-only como `buyers`, `sales` o configuracion
- `403` cuando la empresa tiene desactivado el modulo de recogidas o recogidas al por mayor
- `404` cuando el recurso existe pero no pertenece al ambito visible del usuario autenticado

## 9. Flujo de planificacion semanal (operativo)

1. `generate-week` crea/actualiza `RouteDay` para los dias habilitados de la ruta.
2. Si `regenerate=false`, preserva cualquier `RouteDay` que ya no sea editable.
3. Si `regenerate=true`, valida antes que toda la semana sea editable y aborta completa si no lo es.
4. Para cada dia editable, busca `RouteZoneDay` por `weekday`.
5. Selecciona clientes por geofiltro (`location__within` de los poligonos de zona) y por frecuencia/vencimiento de recogida.
6. Ordena candidatos usando la fecha efectiva mas reciente entre ultima recogida real y ultima planificacion previa.
7. Selecciona por proximidad al hub y a la ultima parada elegida, hasta `max_clients_per_day`; inserta `RouteDayClient` con orden secuencial. La capacidad se usa posteriormente para formar segmentos.
8. Optimiza orden con Google Directions por segmentos de capacidad:
- origen: `CompanyHub.location`
- waypoints: clientes con ubicacion
- cada segmento se optimiza con salida y vuelta al hub
- si Google falla en un bloque, se conserva el orden local de ese bloque dentro de los segmentos calculados y se registra `FALLBACK`
- las paradas sin ubicacion se rechazan al optimizar; se registra `FAILED` y se lanza un error de validacion
- si la capacidad obliga a segmentar la jornada, inserta el hub entre segmentos al exportar navegacion
- la navegacion exportada empieza en el hub y termina tambien en el hub
9. Reescribe `order` en `RouteDayClient`.
10. Crea/actualiza `CollectionRequest` por parada:
- `expires_at = inicio_route_day - 36 horas`
- programa tarea Celery `auto_estimate_collection_request_liters` con `eta=expires_at`
- si `expires_at <= now`, se encola inmediata
- se encola email `notify_collection_request_created`

## 10. Modelo CollectionRequest (campos relevantes)

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

## 11. Valores enumerados importantes

- `PickupFrequency`: `WEEKLY`, `2_WEEKS`, `3_WEEKS`, `4_WEEKS`
- `RouteOptimizationStatus`: `PENDING`, `OPTIMIZED`, `FALLBACK`, `FAILED`
- `RouteDayStatus`: `PLANNED`, `IN_PROGRESS`, `COMPLETED`, `PARTIAL`, `CANCELED`
- `CollectionRequestStatus`: `PENDING`, `ANSWERED`, `AUTO_ESTIMATED`, `MANUAL`
- `PlannedSource`: `CLIENT`, `AUTO`, `MANUAL`
- `ContainerType`: `BIDONES`, `IBC`
- `QuantityUnit`: `KG`, `UD`, `L`
- `BulkCollectionCalculationMode`: `TOTAL`, `UNIT_PRICE`, `QUANTITY`

## 11.1 Recogidas al por mayor y estadisticas

- CRUD owner-only: `/bulk-collections/`
- acepta JSON y `multipart/form-data`
- `invoice_file` admite facturas PDF, JPG o PNG de hasta 10 MB
- deben enviarse dos valores validos entre `quantity`, `unit_price` y `total_price`; `calculation_mode` indica cual recalcula el backend
- las recogidas al por mayor con `billable=true` se incorporan a los costes economicos
- `GET /sales/economic-summary/` devuelve `bought_quantities` y `sold_quantities` equivalentes en `L` y `KG`, tanto en el total como en cada elemento de `monthly`
- las cantidades se normalizan primero a litros con `oil_density_kg_per_liter` y despues se expresan en la unidad seleccionada
- las cantidades expresadas en unidades (`UD`) de ventas y recogidas al por mayor se excluyen de estadisticas fisicas y se cuentan en `ignored_quantities`; sus importes siguen computando cuando corresponda
- las lineas de venta se agregan por su propia unidad; las ventas antiguas sin lineas usan la unidad de la venta principal

## 12. Ejemplos rapidos (curl)

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

### Cliente responde solicitud por envases
```bash
curl -X POST http://localhost:8000/collections/requests/55/answer/ \
  -H "Authorization: Bearer <token_cliente>" \
  -H "Content-Type: application/json" \
  -d '{"container_type":"BIDONES","container_number":3}'
```

### Worker/Owner carga manual
```bash
curl -X POST http://localhost:8000/collections/requests/55/manual/ \
  -H "Authorization: Bearer <token_owner_o_worker>" \
  -H "Content-Type: application/json" \
  -d '{"final_liters":"240.00"}'
```

## 13. Recomendacion de uso

- Para contrato exacto de schemas, usa siempre `GET /schema/` o `GET /docs/`.
- Esta guia sirve como referencia funcional y de negocio de la API real del proyecto.

## 14. Contratos actualizados de rutas, recogidas y compras

### 14.1 Capacidad por defecto y resultado de optimizacion

El CRUD de rutas admite `default_capacity_liters` nullable. La lectura expone
`default_daily_capacity_liters`: primero capacidad explicita de la ruta y, si
no existe, capacidad del camion del trabajador asignado. Para una jornada,
`daily_capacity_liters` propia tiene prioridad. En generacion con `days`, las
fechas no incluidas conservan su capacidad o usan ese valor por defecto.
El payload de `generate-week` sigue requiriendo capacidad global o `days`.

`generate-week` y `operational-overview` devuelven por jornada
`optimization_status`, `optimization_message` y `optimized_at`:

| Estado | Significado |
| --- | --- |
| `PENDING` | Aun no se ha registrado un resultado. |
| `OPTIMIZED` | Optimizacion correcta o innecesaria por menos de dos paradas. |
| `FALLBACK` | Google falla; se usa el orden local por proximidad y capacidad en los bloques afectados. |
| `FAILED` | Falta hub, API key, coordenadas o el resultado segmentado es invalido. |

Falta de hub o key conserva el orden sin bloquear la generacion. Una parada sin
coordenadas se rechaza con `ValueError` en la funcion de optimizacion; si llega
al endpoint de generacion devuelve `400`. La generacion es transaccional, por
lo que un fallo que revierte la transaccion puede revertir tambien la metadata.
`optimized_at` registra el momento del resultado, incluso si fue fallido.

### 14.2 Medicion final de recogidas

`estimated_liters` queda fijado al crear la recogida a partir de sus envases.
`measured_liters` es la cantidad final pagable, no una medida bruta a descontar.
`deduction_liters` es de solo lectura y se calcula como
`max(0, estimated_liters - measured_liters)`. Si el descuento es positivo,
`deduction_reason` es obligatorio (`WATER`, `RESIDUE`, `MIXED`, `OTHER`);
si no hay descuento se limpia el motivo. Sin medicion se limpia el descuento.

`total_price = measured_liters * price_per_liter` cuando hay medicion;
sin medicion usa la estimacion; una recogida cancelada tiene total cero.
`CONFIRMED` exige medicion. En escritura, enviar medicion sin estado explicito
normaliza el estado a `CONFIRMED`. En lectura, `status` es la etiqueta y
`status_code` contiene el codigo del enum.

Ejemplo: estimacion inicial 120 L (dos bidones), medicion final 90 L, precio 0.50 EUR/L:
descuento calculado 30 L e importe 45.00 EUR. Se envia el motivo, pero no se
vuelven a restar esos 30 L de la medicion final.

### 14.3 CRUD de recogidas al por mayor

`GET/POST /bulk-collections/` y `GET/PUT/PATCH/DELETE /bulk-collections/{id}/`.
Requiere JWT, owner de la empresa y modulo habilitado; `company` se asigna en
backend y es de solo lectura. El cliente debe estar vinculado a esa empresa.

Campos: `client`, `collection_date`, `unit`, `calculation_mode`, `quantity`,
`unit_price`, `total_price`, `billable` (por defecto `true`), `notes` e
`invoice_file` opcional. Filtros: `client` (id), `unit`, `billable`, `start_date`,
`end_date` y `search` (nombre, CIF o notas). Usa paginacion global.

| `calculation_mode` | Valores de entrada positivos | Valor calculado |
| --- | --- | --- |
| `TOTAL` (defecto) | `quantity`, `unit_price` | `total_price = quantity * unit_price` |
| `UNIT_PRICE` | `quantity`, `total_price` | `unit_price = total_price / quantity` |
| `QUANTITY` | `unit_price`, `total_price` | `quantity = total_price / unit_price` |

Cantidad e importe tienen dos decimales, precio unitario cuatro; se redondea
con `ROUND_HALF_UP`. `UD` exige cantidad entera. En PATCH pueden reutilizarse
los valores existentes; el campo calculado se recalcula siempre al guardar.

```json
{
  "client": 1,
  "collection_date": "2026-10-09",
  "unit": "L",
  "calculation_mode": "TOTAL",
  "quantity": "3750.00",
  "unit_price": "0.4500",
  "billable": true,
  "notes": "Compra directa"
}
```

Resultado calculado: `total_price = "1687.50"`. Para adjuntar factura, enviar
`multipart/form-data`; `invoice_file` admite PDF, JPEG o PNG hasta 10 MiB.

### 14.4 Cantidades y costes del resumen economico

`bought_quantities` y `sold_quantities` contienen equivalencias `L` y `KG` con
cuatro decimales. Conversion: `L = KG / oil_density_kg_per_liter` y
`KG = L * oil_density_kg_per_liter`. No existe conversion fisica para `UD`.
`ignored_quantities` cuenta filas no convertibles de `bulk_collections` y
`sales`; aparece en el total y por mes. `conversion` informa de la unidad base
`L` y densidad utilizada. `total_bought_volume` y `total_sold_volume` mantienen
compatibilidad como volumen en litros.

El coste al por mayor filtra `billable=true`; su volumen incluye todos los
registros convertibles del periodo. Las recogidas ordinarias se agregan
confirmadas y facturables. Las ventas usan las unidades de sus lineas; si no
hay lineas se usa la cantidad/unidad de la venta principal.

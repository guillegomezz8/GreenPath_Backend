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
- `company`: empresa, hub y configuracion operativa global.
- `zones`: zonas geograficas de recogida.
- `routes`: rutas plantilla, dias operativos y paradas planificadas.
- `collections`: recogidas reales y solicitudes previas de estimacion.
- `sales`: compradores internos, ventas, facturas PDF y resumen economico.

## Estado actual

Actualmente estan operativos:

- CRUD de clientes, trabajadores, camiones y zonas.
- Configuracion de rutas y zonas por dia.
- Generacion semanal de rutas operativas con `generate-week`.
- Ejecucion de `RouteDay`: iniciar, registrar parada, finalizar y exportar navegacion.
- `CollectionRequest` con expiracion, trazabilidad y tareas Celery.
- Estadisticas y panel operativo ya integrados en la API.
- Configuracion global por empresa con precio por litro, hub y datos de facturacion.
- Modulo interno de compradores (`buyers`) solo para owner.
- Modulo de ventas (`sales`) con numero de factura manual, una sola fecha operativa (`invoice_date`) y generacion de PDF.
- Resumen economico con costes de recogidas, ingresos por ventas y beneficio neto.

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

## Configuracion global de empresa

Endpoint principal:

- `GET /companies/settings/`
- `PUT /companies/settings/`

Comportamiento actual:

- Guarda el `default_price_per_liter` de la empresa.
- Guarda datos fiscales y bancarios para facturacion de ventas:
  - razon social
  - CIF
  - direccion fiscal
  - codigo postal, ciudad y provincia
  - pais
  - telefono
  - email
  - cuenta bancaria
  - Codigo LER
  - pie de factura
- Guarda y actualiza el hub de empresa.
- Se aplica por defecto al crear recogidas manuales.
- Se aplica por defecto al registrar una parada desde una ruta.
- El valor sigue siendo editable luego en cada recogida concreta.

## Compradores y ventas

Endpoints principales:

- `GET/POST /buyers/`
- `GET/PUT/PATCH/DELETE /buyers/{id}/`
- `GET/POST /sales/`
- `GET/PUT/PATCH/DELETE /sales/{id}/`
- `GET /sales/{id}/invoice/download/`
- `POST /sales/{id}/invoice/regenerate/`
- `GET /sales/economic-summary/`

Comportamiento actual:

- Todo el bloque es solo para `owner`.
- `Buyer` es un maestro interno, sin acceso a plataforma.
- `Sale` registra comprador, descripcion, cantidad, unidad, precio unitario, IVA y total.
- El numero de factura es manual.
- La unica fecha visible y funcional es `invoice_date`.
- El PDF se genera con WeasyPrint y puede regenerarse cuando se necesite.
- El resumen economico separa costes de recogidas frente a ingresos por ventas.

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
- `apps/user/fixtures/README.md`

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

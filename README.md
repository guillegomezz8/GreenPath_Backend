# GreenPath Backend

Backend Django de GreenPath, una plataforma para gestionar la recogida de aceite usado, su operacion diaria, su cierre economico y el registro de ventas con facturacion PDF.

## 1. Vision general

GreenPath cubre el ciclo funcional principal del negocio:

1. configuracion de empresa y datos maestros
2. planificacion geografica de rutas
3. generacion semanal de jornadas y paradas
4. solicitud previa de litros al cliente
5. ejecucion diaria de la ruta
6. medicion y cierre economico de recogidas
7. gestion de compradores internos
8. registro de ventas
9. generacion de facturas PDF
10. analitica de costes, ingresos y beneficio

No es solo una API de CRUD. El sistema combina operacion, automatizacion, trazabilidad y reporting.

## 2. Stack principal

- Python 3.11
- Django
- Django REST Framework
- PostgreSQL + PostGIS
- Celery + Redis
- React + Vite en frontend
- Google Directions API para optimizacion de rutas
- Gmail API para notificaciones operativas
- WeasyPrint para facturas PDF
- Docker Compose para entorno local

## 3. Modulos funcionales actuales

- `clients`: clientes, frecuencia de recogida, geolocalizacion e historial
- `workers`: trabajadores, rol operativo y datos de empresa
- `trucks`: flota y asignacion de conductor
- `company`: empresa, hub y configuracion operativa/fiscal global
- `zones`: zonas geograficas de recogida
- `routes`: rutas plantilla, dias operativos y paradas planificadas
- `collections`: solicitudes de recogida y recogidas reales
- `sales`: compradores internos, ventas, facturas PDF y resumen economico

## 4. Capacidades funcionales destacadas

### 4.1 Rutas y operacion

- configuracion de rutas plantilla con un trabajador asignado
- zonas por dia (`RouteZoneDay`)
- generacion semanal con `generate-week`
- control de `regenerate` y proteccion de dias ya operados
- limite por capacidad diaria y por maximo de clientes por dia
- optimizacion opcional con Google Directions
- ejecucion diaria con inicio, registro de parada y cierre de jornada

### 4.2 Solicitudes al cliente

- creacion automatica de `CollectionRequest`
- expiracion basada en `inicio_route_day - 36h`
- respuesta del cliente desde portal
- cierre manual por owner/worker
- autoestimacion con Celery
- notificacion por email cuando Gmail API esta disponible

### 4.3 Recogidas y economia

- recogidas pendientes de medicion, confirmadas o canceladas
- medicion en nave y deducciones
- precio por litro precargado desde configuracion de empresa
- bandera `billable` para decidir si una recogida computa economicamente
- solo las recogidas `CONFIRMED` y `billable=true` entran en costes y agregados economicos

### 4.4 Ventas y facturacion

- modulo owner-only de compradores (`Buyer`)
- modulo owner-only de ventas (`Sale`)
- numero de factura manual
- fecha funcional unica: `invoice_date`
- recalculo backend de subtotal, IVA y total
- PDF de factura descargable y regenerable

### 4.5 Configuracion global de empresa

- precio global por litro
- hub geolocalizado
- razon social
- CIF
- direccion fiscal
- codigo postal, ciudad, provincia y pais
- telefono y email
- cuenta bancaria
- codigo LER
- pie de factura

## 5. Estado funcional actual

Actualmente estan operativos:

- CRUD de clientes, trabajadores, camiones y zonas
- configuracion de rutas y zonas por dia
- generacion semanal de rutas operativas con `POST /routes/{id}/generate-week/`
- ejecucion diaria de `RouteDay`
- solicitudes previas al cliente con expiracion y trazabilidad
- dashboard y estadisticas por rol
- configuracion global por empresa
- recogidas con control de `facturable`
- compradores internos, ventas y facturas PDF
- resumen economico con costes, ingresos y beneficio neto

## 6. Reglas de negocio clave

- solo owner puede generar semana operativa
- `regenerate=true` solo se admite si la semana sigue siendo editable
- los dias ya operados se preservan cuando no se regenera
- la capacidad diaria se aplica de forma estricta
- una parada cancelada cuenta como procesada para cerrar la jornada
- una recogida no facturable sigue existiendo, pero no entra en estadisticas economicas
- las ventas computan como ingreso
- las recogidas confirmadas y facturables computan como coste

## 7. Integraciones externas

### 7.1 Google Maps / Directions

Se utiliza para:

- geocodificar direcciones de clientes
- optimizar el orden de paradas en la generacion semanal
- abrir navegacion desde la pantalla de ejecucion de ruta

### 7.2 Gmail API

Se utiliza para:

- envio de credenciales de acceso
- envio de notificaciones de solicitud de estimacion al cliente

### 7.3 Celery y Redis

Se utilizan para:

- autoestimacion de solicitudes expiradas
- envio de notificaciones asincronas
- tareas programadas y periodicas

## 8. Variables de entorno relevantes

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

- `GMAIL_CLIENT_SECRET_JSON` y `GMAIL_TOKEN_JSON` deben ir en una sola linea dentro de `.env`
- `GMAIL_FROM` no debe llevar espacios adicionales

## 9. Puesta en marcha local

Levantar servicios:

```bash
docker-compose up --build
```

Servicios principales:

- API: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs/`
- OpenAPI schema: `http://localhost:8000/schema/`
- Admin Django: `http://localhost:8000/admin/`

## 10. Fixtures de demo

Para poblar un entorno de pruebas se recomienda cargar, al menos, en este orden:

```bash
python manage.py loaddata \
  apps/user/fixtures/01-users.json \
  apps/user/fixtures/02-companies.json \
  apps/user/fixtures/03-workers.json \
  apps/user/fixtures/04-clients.json \
  apps/user/fixtures/05-routes.json \
  apps/user/fixtures/06-collections.json \
  apps/user/fixtures/07-zones.json \
  apps/user/fixtures/08-truck.json \
  apps/user/fixtures/09-company-hubs.json \
  apps/user/fixtures/10-route-zone-days.json \
  apps/user/fixtures/11-company-settings.json \
  apps/user/fixtures/12-buyers.json \
  apps/user/fixtures/13-sales.json
```

Consulta `apps/user/fixtures/README.md` para el detalle.

## 11. Mapa de documentacion

- `docs/INDICE_DOCUMENTACION.md`: indice general y lectura recomendada
- `docs/FUNCIONAL.md`: especificacion funcional completa del sistema
- `docs/REQUISITOS.md`: catalogo formal de requisitos de negocio, funcionales y no funcionales
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`: APIs externas, configuracion y riesgos de integracion
- `docs/DESPLIEGUE_Y_OPERACION.md`: puesta en marcha, operacion, soporte y continuidad
- `docs/PLANIFICACION_Y_COSTES.md`: metodologia, estimaciones, planificacion y costes
- `docs/MEMORIA_FUNCIONAL_TFG.md`: version orientada a memoria/defensa academica
- `docs/BIBLIOGRAFIA_Y_FUENTES.md`: fuentes tecnicas y referencias para memoria y defensa
- `docs/CASOS_DE_USO.md`: secuencias funcionales por actor
- `docs/MANUAL_USUARIO.md`: manual de uso por rol y recomendaciones
- `docs/API.md`: endpoints, payloads y reglas de API
- `docs/ARQUITECTURA_TECNICA.md`: arquitectura, capas e integraciones
- `docs/FRONTEND_PANTALLAS.md`: inventario y comportamiento del frontend
- `docs/TESTING.md`: estrategia, ejecucion y cobertura actual de tests
- `docs/ROUTE_FLOW.md`: detalle del flujo de rutas y su operacion
- `docs/HISTORIAS_USUARIO.md`: backlog funcional y criterios de aceptacion
- `docs/UML_BD.md`: diagrama UML del modelo de datos y relaciones principales

## 12. Recomendacion de lectura

Si alguien se incorpora al proyecto, el orden recomendado es:

1. `README.md`
2. `docs/INDICE_DOCUMENTACION.md`
3. `docs/FUNCIONAL.md`
4. `docs/REQUISITOS.md`
5. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
6. `docs/PLANIFICACION_Y_COSTES.md`
7. `docs/MEMORIA_FUNCIONAL_TFG.md`
8. `docs/CASOS_DE_USO.md`
9. `docs/MANUAL_USUARIO.md`
10. `docs/ARQUITECTURA_TECNICA.md`
11. `docs/API.md`
12. `docs/FRONTEND_PANTALLAS.md`
13. `docs/TESTING.md`
14. `docs/UML_BD.md`

## 13. Estado y siguientes mejoras naturales

El sistema esta funcionalmente avanzado y cubre el flujo principal del negocio.
Las siguientes mejoras naturales, fuera del alcance actual, serian:

- ampliar tests automatizados end-to-end
- endurecer concurrencia distribuida en generacion semanal para despliegues multi-instancia
- ampliar reporting avanzado
- integrar contabilidad o exportaciones financieras externas

## 14. Validacion rapida recomendada

Cuando se retome el proyecto o se quiera revisar su salud minima, conviene ejecutar al menos:

### Backend

```bash
python manage.py check
python manage.py check --tag admin
python manage.py makemigrations --check --dry-run
```

### Frontend

```bash
npm run build
```

### Revision funcional minima

Se recomienda comprobar manualmente:

- login por rol
- generacion semanal de rutas
- ejecucion diaria de una jornada
- medicion y confirmacion de una recogida
- alta de una venta y descarga de su factura PDF
- dashboard y estadisticas economicas

## 15. Testing automatizado actual

GreenPath ya dispone de una base real de tests automatizados en backend y frontend.
Para el detalle operativo completo conviene consultar tambien `docs/TESTING.md`.

### Backend

La suite backend esta organizada por modulo y vive principalmente en:

- `apps/auth/tests/`
- `apps/base/tests.py` y `apps/base/test_utils.py`
- `apps/company/tests/`
- `apps/truck/tests/`
- `apps/zone/tests/`
- `apps/user/tests/`
- `apps/collection/tests/`
- `apps/route/tests/`
- `apps/sale/tests/`

Cobertura funcional actual destacada:

- autenticacion y permisos base
- company settings y hub
- camiones y reasignacion de conductor
- zonas y filtros de busqueda
- clientes y trabajadores
- recogidas y `billable`
- generacion semanal y cierre de jornada
- compradores, ventas y resumen economico

Comando recomendado dentro del contenedor backend:

```bash
python manage.py test apps.auth.tests apps.base.tests apps.company.tests apps.truck.tests apps.zone.tests apps.user.tests apps.collection.tests apps.route.tests apps.sale.tests
```

### Frontend

La suite frontend usa `Vitest + Testing Library` y vive en `src/**/__tests__/`.

Cobertura funcional actual destacada:

- `buyers`: estado vacio y filtro base
- `sales`: formulario y detalle
- `collections`: detalle economico y traducciones
- `clients`: historial y badges facturables
- `routes`: `GenerateWeekDialog`
- `settings`: guardado independiente por seccion
- `stats`: resumen economico
- `trucks`: listado vacio
- `profile`: perfil owner sin campos impropios
- `workers`: alta y edicion sin exponer rol/company

Comando recomendado en frontend:

```bash
npm run test
```

Si el entorno local da problemas con `node_modules`, la ejecucion en contenedor temporal de Node suele ser la via mas estable.

### Snapshot de cobertura a fecha 2026-04-05

- backend: `25` tests verdes
- frontend: `17` tests verdes

No sustituyen a una suite E2E completa, pero ya cubren reglas de negocio y UX que antes solo estaban protegidas por revision manual.

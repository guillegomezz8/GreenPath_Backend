# GreenPath Backend

Backend de GreenPath, una plataforma full-stack multiempresa para la gestion integral de empresas dedicadas a la recogida de aceite usado. La API centraliza configuracion de empresa, clientes, trabajadores, camiones, zonas, rutas, recogidas, ventas, facturacion y analitica economica en un unico flujo operativo.

El proyecto esta desarrollado como Trabajo de Fin de Grado y busca resolver un problema real de digitalizacion: sustituir procesos dispersos en hojas de calculo, llamadas, documentos sueltos y conocimiento informal por una solucion trazable, medible y conectada.

## Indice

- [Vision funcional](#vision-funcional)
- [Stack tecnico](#stack-tecnico)
- [Arquitectura del backend](#arquitectura-del-backend)
- [Roles de usuario](#roles-de-usuario)
- [Modulos principales](#modulos-principales)
- [Integraciones externas](#integraciones-externas)
- [Puesta en marcha](#puesta-en-marcha)
- [Variables de entorno](#variables-de-entorno)
- [Endpoints y documentacion API](#endpoints-y-documentacion-api)
- [Fixtures de demo](#fixtures-de-demo)
- [Comandos utiles](#comandos-utiles)
- [Documentacion del TFG](#documentacion-del-tfg)

## Vision funcional

GreenPath cubre el ciclo principal de una empresa de recogida de aceite usado:

1. Configuracion fiscal, operativa y geografica de la empresa.
2. Alta de clientes, trabajadores, camiones y zonas de recogida.
3. Definicion de rutas plantilla y asignacion de zonas por dia.
4. Generacion semanal de jornadas operativas.
5. Solicitud previa de estimacion de litros al cliente.
6. Ejecucion diaria de rutas con paradas, incidencias y cierre.
7. Consolidacion de recogidas, litros reales y coste asociado.
8. Gestion de compradores y ventas.
9. Generacion de facturas PDF bajo demanda.
10. Consulta de estadisticas operativas y economicas.

La clave funcional del proyecto es unir tres capas que normalmente aparecen separadas:

- Administracion: usuarios, empresas, clientes, trabajadores y configuracion.
- Operacion/logistica: zonas, rutas, jornadas, paradas y recogidas.
- Economia/documentacion: costes, ventas, facturas PDF y resumen economico.

## Stack tecnico

### Backend

- Python 3.11
- Django 5
- Django REST Framework
- Django Filter
- Simple JWT
- drf-spectacular
- django-simple-history

### Base de datos y geodatos

- PostgreSQL
- PostGIS
- GDAL
- Shapely
- GeoJSON
- pyproj
- geopy

### Procesos e infraestructura

- Docker
- Docker Compose
- Celery
- Celery Beat
- Redis
- Flower
- Gunicorn
- WhiteNoise

### Integraciones

- Google Maps Platform / Directions API
- Google OAuth
- Gmail API
- WeasyPrint

## Arquitectura del backend

El backend esta organizado por dominios funcionales dentro de `apps/`:

```text
apps/
  base/          Utilidades comunes, literales, paginacion, health check y Celery
  user/          Usuarios, owners, workers, clients, autenticacion local y perfiles
  company/       Empresas, hub logistico y configuracion fiscal/operativa
  zone/          Zonas geograficas de recogida
  route/         Rutas plantilla, jornadas operativas, paradas y navegacion
  collection/    Solicitudes de recogida, recogidas reales y consolidacion
  bulk_collection/ Recogidas al por mayor, adjuntos y calculos economicos
  sale/          Compradores, ventas, importes y facturas PDF
  truck/         Camiones y asignacion de conductores
global/          Settings, urls, celery, wsgi/asgi
templates/       Plantillas HTML para documentos
static/          Recursos estaticos
docs/            Documentacion funcional y tecnica del TFG
```

La API usa autenticacion JWT, paginacion personalizada, filtros por query params y documentacion OpenAPI generada automaticamente.

## Roles de usuario

- `owner`: administra la empresa, usuarios, configuracion, rutas, economia, ventas, facturacion y estadisticas.
- `worker`: opera rutas asignadas, registra paradas y gestiona recogidas durante la ejecucion diaria.
- `client`: consulta sus solicitudes, responde estimaciones y revisa su historico.
- `buyer`: entidad comercial interna usada para ventas y facturas; no es un rol de acceso a la aplicacion.

## Modulos principales

### Empresa y configuracion

- Datos fiscales y de contacto.
- Precio global por litro.
- Hub logistico geolocalizado.
- Codigo LER y pie de factura.
- Configuracion usada por recogidas, ventas y facturas.

### Clientes, trabajadores y camiones

- CRUD de clientes y trabajadores.
- Perfil operativo por rol.
- Geocodificacion de direcciones de clientes.
- Alta y asignacion de camiones a conductores.
- Historico mediante `django-simple-history`.

### Zonas

- Gestion de zonas geograficas.
- Asociacion de clientes a zonas.
- Uso de zonas para construir rutas y jornadas semanales.

### Rutas y operacion diaria

- Rutas plantilla con trabajador asignado.
- Configuracion de zonas por dia mediante `RouteZoneDay`.
- Generacion semanal con `POST /routes/{id}/generate-week/`.
- Proteccion de jornadas ya operadas.
- Uso controlado de `regenerate`.
- Capacidad diaria y limite funcional de clientes por jornada.
- Optimizacion opcional con Google Directions.
- Plan operativo con retornos al hub cuando la capacidad lo exige.
- Exportacion de enlaces de navegacion a Google Maps.
- Inicio, registro de parada y cierre de jornada.

### Solicitudes y recogidas

- Creacion automatica de `CollectionRequest`.
- Respuesta del cliente desde su portal.
- Expiracion de solicitudes segun fecha de jornada.
- Autoestimacion asincrona con Celery.
- Cierre manual por owner o worker.
- Recogidas pendientes de medicion, confirmadas o canceladas.
- Campo `billable` para separar dato operativo de impacto economico.

### Ventas y facturacion

- CRUD owner-only de compradores (`Buyer`).
- CRUD owner-only de ventas (`Sale`).
- Numero de factura manual y unico por empresa.
- Fecha funcional `invoice_date`.
- Recalculo backend de subtotal, IVA y total.
- Foto fiscal del emisor vinculada a la venta para conservar datos de empresa y cuenta bancaria historicos.
- Descarga de factura PDF generada al vuelo con WeasyPrint.

### Estadisticas

- Resumen economico.
- Costes por recogidas confirmadas y facturables.
- Ingresos por ventas.
- Beneficio neto.
- Indicadores operativos para dashboard.

## Integraciones externas

### Google Maps Platform

Se utiliza para geocodificar clientes, optimizar el orden de paradas, generar planes de navegacion y abrir enlaces externos de Google Maps desde la ejecucion de rutas.

### Google OAuth

Permite autenticacion social mediante ID token de Google, validado en backend contra los client IDs configurados.

### Gmail API

Se usa para enviar credenciales y notificaciones asociadas a solicitudes de estimacion cuando la configuracion esta disponible.

### Celery, Redis y Flower

Celery ejecuta tareas asincronas y periodicas, Redis actua como broker/backend de resultados y Flower permite monitorizar workers y tareas.

### WeasyPrint

Renderiza facturas PDF desde plantillas HTML/CSS sin persistir binarios innecesarios.

## Puesta en marcha

### Requisitos

- Docker Desktop
- Docker Compose o Docker Compose V2
- Archivo `.env` configurado en la raiz del backend
- `ngrok.exe` en la raiz del backend si se quiere exponer la API con el lanzador del escritorio

### Arranque con Docker

Desde `E:\UNIVERSIDAD\TFG\GreenPath_Backend`:

```bash
docker compose up --build
```

Para arrancar contenedores ya creados:

```bash
docker compose start
```

Servicios principales:

- API: `http://localhost:8000/`
- Health check: `http://localhost:8000/health/`
- Swagger: `http://localhost:8000/docs/`
- OpenAPI schema: `http://localhost:8000/schema/`
- Admin Django: `http://localhost:8000/admin/`
- Flower: `http://localhost:5555/`

### Arranque conjunto con frontend y ngrok

El archivo `start_greenpath.bat` del escritorio levanta backend, frontend y ngrok:

```text
C:\Users\usuario\OneDrive\Escritorio\start_greenpath.bat
```

URLs esperadas:

- Backend local: `http://localhost:8000`
- Frontend local: `http://localhost:5173`
- Ngrok backend: `https://epic-supreme-panther.ngrok-free.app`

Si falla el arranque por puertos ocupados, revisa si hay otros proyectos usando `8000`, `5432`, `6379`, `5555` o `5173`.

## Variables de entorno

Variables principales del backend:

```env
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=
CORS_ALLOW_ALL_ORIGINS=
CORS_ALLOWED_ORIGINS=
CORS_ALLOWED_ORIGIN_REGEXES=
SECURE_SSL_REDIRECT=
SESSION_COOKIE_SECURE=
CSRF_COOKIE_SECURE=

DATABASE_URL=
DB_ENGINE=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_CONN_MAX_AGE=
MEDIA_ROOT=
SECURE_REFERRER_POLICY=

CELERY_BROKER_URL=
CELERY_RESULT_BACKEND=
REDIS_URL=

GOOGLE_CLIENT_ID=
GOOGLE_MAPS_API_KEY=

SMTP_SERVER=
SMTP_PORT=
EMAIL_USER=
EMAIL_PASSWORD=
EMAIL_USE_TLS=
EMAIL_USE_SSL=

GMAIL_FROM=
GMAIL_CLIENT_SECRET_JSON=
GMAIL_TOKEN_JSON=
```

Notas:

- `GMAIL_CLIENT_SECRET_JSON` y `GMAIL_TOKEN_JSON` deben guardarse en una sola linea dentro de `.env`.
- Las listas de dominios y origenes aceptan valores separados por espacios o comas.
- `DATABASE_URL` tiene prioridad sobre las variables `DB_*` y siempre usa el backend PostGIS.
- `REDIS_URL` se usa como valor comun de Celery salvo que se definan `CELERY_BROKER_URL` o `CELERY_RESULT_BACKEND`.
- En produccion, configura `CORS_ALLOWED_ORIGINS` con el origen exacto del frontend y deja `CORS_ALLOW_ALL_ORIGINS=0`.
- `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` deben incluir el dominio publico del backend si se expone la API.
- En Docker, `DB_HOST` y las URLs de Redis deben apuntar a los nombres de servicio del `docker-compose.yml`.
- El frontend consume la API mediante `VITE_APP_API_URL`.
- La receta completa de Railway esta en `docs/DESPLIEGUE_Y_OPERACION.md`.

## Endpoints y documentacion API

Entradas principales del backend:

- `POST /login/`
- `POST /logout/`
- `POST /token/refresh/`
- `POST /authenticate/login`
- `/users/`
- `/workers/`
- `/clients/`
- `/companies/`
- `/zones/`
- `/trucks/`
- `/routes/`
- `/collections/`
- `/bulk-collections/`
- `/buyers/`
- `/sales/`

Documentacion generada:

- Swagger UI: `http://localhost:8000/docs/`
- OpenAPI schema: `http://localhost:8000/schema/`

Documentacion escrita:

- `docs/API.md`
- `docs/FUNCIONAL.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/FRONTEND_PANTALLAS.md`

## Fixtures de demo

Para poblar un entorno de pruebas se recomienda cargar los fixtures en este orden:

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

Consulta `apps/user/fixtures/README.md` para el detalle del dataset.

El dataset incluye vehiculos, clientes por zonas, rutas, recogidas, configuracion de empresa, compradores y ventas coherentes con las estadisticas economicas.

## Demo comercial con muchos datos

Para anadir una empresa independiente con 80 clientes, 1104 recogidas,
6 rutas, 96 ventas y el resto de modulos preparados para presentaciones:

```bash
docker compose exec web python manage.py load_demo_data
```

Carga [demo_datos.json](apps/user/fixtures/demo_datos.json) sin modificar
los datos existentes y omite la carga si esa demo ya existe. El owner es
`propietario@demo.com` y la contrasena inicial `pass12345`.
Usa `--dry-run` para validar sin guardar o `--namespace demo-octubre` para crear
otra empresa demo. Consulta [la guia de fixtures](apps/user/fixtures/README.md)
para cuentas worker/client, opciones y formato del JSON.

## Comandos utiles

Comprobar configuracion Django:

```bash
python manage.py check
```

Aplicar migraciones:

```bash
python manage.py migrate
```

Crear superusuario:

```bash
python manage.py createsuperuser
```

Levantar servidor Django sin Docker:

```bash
python manage.py runserver 0.0.0.0:8000
```

Ejecutar worker Celery:

```bash
celery -A global worker --loglevel=info
```

Ejecutar beat Celery:

```bash
celery -A global beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Abrir Flower:

```bash
celery -A global flower --port=5555 --basic_auth=admin:adminpassword
```

## Reglas de negocio destacadas

- Solo `owner` puede generar semanas operativas.
- `regenerate=true` solo se admite cuando la semana sigue siendo editable.
- Los dias ya operados se preservan si no se regenera.
- La capacidad divide la jornada en tramos con retorno al hub; la seleccion de clientes se limita por `max_clients_per_day`, frecuencia y geografia.
- Una parada cancelada cuenta como procesada para poder cerrar la jornada.
- Una recogida no facturable existe a nivel operativo, pero no entra en estadisticas economicas.
- Las ventas computan como ingreso.
- Las recogidas confirmadas y facturables y las recogidas al por mayor facturables computan como coste.
- `measured_liters` son litros finales pagables; el descuento se calcula como la diferencia positiva frente a la estimacion inicial.
- Las lineas de venta aceptan precios unitarios con hasta ocho decimales; los importes finales se redondean a dos.
- `UD` no se convierte a litros o kilogramos en estadisticas de cantidades.
- La factura PDF se genera bajo demanda, pero los datos fiscales del emisor se toman del snapshot guardado en la venta.

## Documentacion del TFG

La documentacion principal se mantiene en `docs/`. Documentos recomendados:

- `docs/INDICE_DOCUMENTACION.md`
- `docs/FUNCIONAL.md`
- `docs/REQUISITOS.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/API.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
- `docs/ROUTE_FLOW.md`
- `docs/TESTING.md`
- `docs/MEMORIA_FUNCIONAL_TFG.md`
- `docs/PLANIFICACION_Y_COSTES.md`
- `docs/UML_BD.md`

Lectura recomendada para entender el proyecto completo:

1. `README.md`
2. `docs/INDICE_DOCUMENTACION.md`
3. `docs/FUNCIONAL.md`
4. `docs/ARQUITECTURA_TECNICA.md`
5. `docs/API.md`
6. `docs/FRONTEND_PANTALLAS.md`
7. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
8. `docs/TESTING.md`
9. `docs/MEMORIA_FUNCIONAL_TFG.md`

## Valor del proyecto

GreenPath no es un CRUD aislado. Es una plataforma que conecta operacion real, logistica, economia, documentacion e integraciones externas. Su valor tecnico esta en la combinacion de API REST, geolocalizacion, optimizacion de rutas, procesos asincronos, facturacion PDF, autenticacion por roles y una base documental preparada para justificar el alcance funcional de un TFG.

## Recogidas al por mayor

`apps/bulk_collection` expone `/bulk-collections/` para el owner de la empresa.
Admite cantidades en `KG`, `L` o `UD`, factura adjunta y calculo de cantidad,
precio unitario o importe a partir de los otros dos valores. El acceso depende
de `CompanySettings.bulk_collections_enabled`, gestionado desde Django Admin.
El modulo de recogidas ordinarias depende de `collections_enabled`.

Consulta [API](docs/API.md) para payloads, filtros, calculos y resumen economico.

## Primer arranque y comprobaciones

El entrypoint local no aplica migraciones automaticamente. Con los servicios
levantados, ejecutar antes de usar la API:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py check
```

En Docker, usa `DB_HOST=my-postgres` y `REDIS_URL=redis://redis:6379/0`.
Para un proceso ejecutado en el host, Redis publicado por este Compose usa
`redis://localhost:6379/0`; el fallback de settings (`localhost:8004`) no coincide
con ese puerto, por lo que debe configurarse expresamente.
El frontend se arranca por separado desde el proyecto hermano `GreenPath_Frontend`.
Los scripts del escritorio y las URLs de ngrok son propios de cada instalacion.
`GET /health/` devuelve `{"status":"ok"}` y solo comprueba respuesta HTTP del
proceso; no consulta PostGIS, Redis ni servicios externos.

Pruebas backend completas (en base de datos de test):

```bash
docker compose exec web python manage.py test apps.auth.tests apps.base.tests apps.company.tests apps.truck.tests apps.zone.tests apps.user.tests apps.collection.tests apps.bulk_collection.tests apps.route.tests apps.sale.tests --noinput
```

# GreenPath Backend

Backend Django de GreenPath, una plataforma web multiempresa para la gestion integral de empresas dedicadas a la recogida de aceite usado. El sistema no se limita a registrar recogidas: conecta configuracion de empresa, clientes, trabajadores, zonas, rutas, operacion diaria, recogidas, ventas, facturacion PDF y analitica economica dentro de una unica solucion.

## 1. Contexto del proyecto

GreenPath nace de una necesidad real de digitalizacion. En este tipo de empresas es habitual que una parte importante de la operacion se gestione con hojas de calculo, conversaciones telefonicas, conocimiento informal del responsable de ruta, documentos sueltos y herramientas externas no conectadas entre si. Eso dificulta responder con precision a preguntas basicas:

- que clientes deben recogerse esta semana
- que se ha ejecutado realmente en calle
- cuanto volumen se ha recogido y cuanto se ha vendido
- que parte de las recogidas computa economicamente
- cual es el beneficio real del periodo
- como justificar de forma trazable una factura o una ruta operativa

El proyecto se plantea como una respuesta integral a ese problema. No es un CRUD academico aislado, sino una plataforma que intenta reflejar el trabajo diario de una empresa real y convertirlo en un flujo digital, trazable y medible.

## 2. Vision general

GreenPath cubre el ciclo funcional principal del negocio:

1. configuracion de empresa y datos maestros
2. definicion geografica de zonas y rutas plantilla
3. generacion semanal de jornadas y paradas
4. solicitud previa de envases al cliente con litros calculados
5. ejecucion diaria de la ruta
6. medicion posterior en nave y consolidacion economica de la recogida
7. gestion de compradores internos
8. registro de ventas
9. generacion bajo demanda de facturas PDF
10. explotacion de estadisticas operativas y economicas

La idea clave es que el sistema una en una sola plataforma tres capas que en el negocio real suelen vivir separadas:

- capa administrativa
- capa operativa y logistica
- capa economica y documental

## 3. Enfoque multiempresa y roles

La aplicacion se ha planteado como una solucion multiempresa. Cada empresa opera sobre su propio conjunto de datos y permisos:

- clientes
- trabajadores
- camiones
- zonas
- rutas
- recogidas
- compradores
- ventas
- configuracion fiscal y operativa
- estadisticas

Roles y entidades principales:

- `owner`: control global del negocio, configuracion, rutas, economia, ventas y reporting
- `worker`: operacion diaria, rutas y recogidas
- `client`: solicitudes propias, historico y perfil
- `buyer`: entidad comercial interna para ventas y facturacion; no es un rol de acceso a la plataforma

## 4. Stack principal

### 4.1 Backend y persistencia

- Python 3.11
- Django
- Django REST Framework
- Django Filter
- PostgreSQL
- PostGIS

### 4.2 Procesos e infraestructura

- Celery
- Redis
- Docker
- Docker Compose
- Flower

### 4.3 Frontend relacionado

- React
- Vite
- Tailwind CSS
- Leaflet / React Leaflet

### 4.4 APIs y librerias de terceros consumidas

- Google Maps Platform / Directions API
- Gmail API
- WeasyPrint

Estas integraciones son parte importante del valor tecnico del TFG porque introducen geocodificacion, optimizacion de rutas, apertura de navegacion externa, envio real de correos y generacion documental en PDF con formato profesional.

## 5. Modulos funcionales actuales

- `clients`: clientes, frecuencia, geolocalizacion e historico
- `workers`: trabajadores, rol operativo y relacion con empresa
- `trucks`: flota y asignacion de conductor
- `company`: empresa, hub y configuracion operativa/fiscal
- `zones`: zonas geograficas de recogida
- `routes`: rutas plantilla, dias operativos, paradas y ejecucion diaria
- `collections`: solicitudes de recogida y recogidas reales
- `sales`: compradores internos, ventas, facturacion PDF y resumen economico

## 6. Capacidades funcionales destacadas

### 6.1 Rutas y operacion diaria

- configuracion de rutas plantilla con trabajador asignado
- zonas por dia mediante `RouteZoneDay`
- generacion semanal con `generate-week`
- proteccion de dias ya operados y uso controlado de `regenerate`
- limite de capacidad diaria y maximo funcional de clientes por jornada
- optimizacion opcional con Google Directions
- plan operativo interno por capacidad cuando la carga prevista exige retorno al hub
- navegacion exportada que sale del hub y vuelve al hub al cierre de la jornada
- ejecucion diaria con inicio, registro de parada y cierre de jornada

### 6.2 Solicitudes al cliente

- creacion automatica de `CollectionRequest`
- expiracion basada en la fecha de la jornada
- respuesta del cliente desde su portal
- cierre manual por owner o worker
- autoestimacion asincrona con Celery
- notificacion por email cuando Gmail API esta disponible

### 6.3 Recogidas y cierre economico

- recogidas pendientes de medicion, confirmadas o canceladas
- consolidacion posterior en nave
- precio por litro precargado desde configuracion de empresa
- bandera `billable` para separar dato operativo de impacto economico
- solo las recogidas `CONFIRMED` y `billable=true` computan en costes y agregados

### 6.4 Ventas y facturacion

- modulo owner-only de compradores (`Buyer`)
- modulo owner-only de ventas (`Sale`)
- numero de factura manual y unico por empresa
- fecha funcional unica: `invoice_date`
- recalculo backend de subtotal, IVA y total
- generacion de factura PDF bajo demanda: el fichero no se persiste, se renderiza en cada descarga con el estado vigente de la venta y de la configuracion fiscal

### 6.5 Configuracion global de empresa

- precio global por litro
- hub geolocalizado
- razon social y CIF
- direccion fiscal
- codigo postal, ciudad, provincia y pais
- telefono y email
- cuenta bancaria
- codigo LER
- pie de factura

## 7. Estado funcional actual

Actualmente estan operativos:

- CRUD de clientes, trabajadores, camiones y zonas
- configuracion de rutas y zonas por dia
- generacion semanal de rutas operativas con `POST /routes/{id}/generate-week/`
- ejecucion diaria de `RouteDay`
- solicitudes previas al cliente con expiracion y trazabilidad
- dashboard ejecutivo para owner y estadisticas economicas
- configuracion global por empresa
- recogidas con control de `facturable`
- compradores internos, ventas y facturas PDF
- resumen economico con costes, ingresos y beneficio neto
- documentacion unificada del proyecto en `docs/`

## 8. Reglas de negocio clave

- solo owner puede generar semana operativa
- `regenerate=true` solo se admite si la semana sigue siendo editable
- los dias ya operados se preservan cuando no se regenera
- la capacidad diaria se aplica de forma estricta
- una parada cancelada cuenta como procesada para cerrar la jornada
- una recogida no facturable sigue existiendo, pero no entra en estadisticas economicas
- las ventas computan como ingreso
- las recogidas confirmadas y facturables computan como coste
- el PDF de factura siempre se genera con los datos vigentes en el momento de descarga

## 9. Integraciones externas y valor tecnico

### 9.1 Google Maps / Directions

Se utiliza para:

- geocodificar direcciones de clientes
- optimizar el orden de paradas en la generacion semanal
- abrir navegacion desde la pantalla de ejecucion de ruta
- exportar navegacion alineada con el `operational_plan` y con retornos intermedios al hub cuando la capacidad lo exige

### 9.2 Gmail API

Se utiliza para:

- envio de credenciales de acceso
- envio de notificaciones de solicitud de estimacion al cliente

### 9.3 Celery y Redis

Se utilizan para:

- autoestimacion de solicitudes expiradas
- envio de notificaciones asincronas
- tareas programadas y periodicas

### 9.4 WeasyPrint

Se utiliza para:

- renderizar facturas PDF desde plantillas HTML/CSS
- mantener una salida documental profesional
- generar documentos al vuelo sin almacenar binarios innecesarios

## 10. Variables de entorno relevantes

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GMAIL_FROM`
- `GMAIL_CLIENT_SECRET_JSON`
- `GMAIL_TOKEN_JSON`

Notas:

- `GMAIL_CLIENT_SECRET_JSON` y `GMAIL_TOKEN_JSON` deben ir en una sola linea dentro de `.env`
- `GMAIL_FROM` no debe llevar espacios adicionales
- el frontend usa `VITE_APP_API_URL`, `VITE_GOOGLE_CLIENT_ID` y, si procede, `VITE_GOOGLE_SIGNATURE`

## 11. Puesta en marcha local

Levantar servicios:

```bash
docker-compose up --build
```

Servicios principales:

- API: `http://localhost:8000/`
- Swagger: `http://localhost:8000/docs/`
- OpenAPI schema: `http://localhost:8000/schema/`
- Admin Django: `http://localhost:8000/admin/`
- Flower: `http://localhost:5555/`
- Frontend Vite, levantado desde `D:\TFG\front\GreenPath_Frontend`: `http://localhost:5173/`

## 12. Fixtures de demo

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

Notas del dataset de demo actual:

- 2 vehiculos operativos de ejemplo
- clientes repartidos por zonas reales sin solapes funcionales entre municipios
- recogidas recientes concentradas en fechas cercanas para probar generacion y estadisticas
- ventas de ejemplo ajustadas para mantener coherencia entre volumen comprado confirmado/facturable y volumen vendido

## 13. Estado de la documentacion

La documentacion principal del proyecto se mantiene unificada en la carpeta `docs/` del backend. No se limita a explicar endpoints, sino que cubre negocio, requisitos, arquitectura, testing, despliegue, integraciones, frontend, manual de usuario, planificacion y modelo de datos.

Documentos especialmente importantes:

- `docs/FUNCIONAL.md`
- `docs/REQUISITOS.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/API.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
- `docs/MEMORIA_FUNCIONAL_TFG.md`
- `docs/PLANIFICACION_Y_COSTES.md`
- `docs/UML_BD.md`

## 14. Mapa de lectura recomendado

Si vienes nuevo al proyecto:

1. `README.md`
2. `docs/INDICE_DOCUMENTACION.md`
3. `docs/FUNCIONAL.md`
4. `docs/ARQUITECTURA_TECNICA.md`
5. `docs/API.md`
6. `docs/FRONTEND_PANTALLAS.md`
7. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
8. `docs/REQUISITOS.md`
9. `docs/TESTING.md`
10. `docs/MEMORIA_FUNCIONAL_TFG.md`

## 15. Valor del proyecto

GreenPath tiene valor por tres razones principales:

- resuelve un problema real de digitalizacion empresarial
- combina operacion, logistica, economia y documentacion en una sola herramienta
- incorpora varias librerias y APIs consumidas que elevan claramente la complejidad tecnica del TFG

En conjunto, el proyecto ya no debe leerse como una API de gestion basica, sino como una plataforma full-stack con alcance funcional amplio, integraciones reales y una base documental suficiente para una memoria de TFG extensa y defendible.

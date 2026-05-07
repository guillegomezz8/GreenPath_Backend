# Despliegue y Operacion GreenPath

Fecha de revision: 2026-04-30

## 1. Objetivo del documento

Este documento recoge el enfoque de despliegue, puesta en marcha, operacion y soporte de GreenPath.
Su finalidad es complementar la documentacion funcional y tecnica con una vision mas cercana a explotacion real del sistema.

Se centra en:

- estructura de servicios
- variables de entorno
- puesta en marcha local
- recomendaciones de despliegue
- operacion diaria
- observabilidad y soporte
- backup, recuperacion y continuidad

La revision actual contempla el alcance completo de GreenPath: backend, frontend, PostGIS, Celery, Redis, Gmail API, Google Maps Platform, WeasyPrint, facturacion bajo demanda y datos de demostracion para defensa del TFG.

## 2. Vision general del entorno

GreenPath se ha trabajado con una arquitectura separada en frontend, backend, base de datos y servicios auxiliares.

En entorno local y de demostracion, el proyecto funciona sobre contenedores Docker coordinados con Docker Compose.

Los bloques principales son:

- frontend React + Vite
- backend Django + Django REST Framework
- base de datos PostgreSQL con PostGIS
- Redis como broker y soporte de tareas asincronas
- Celery para tareas diferidas y periodicas
- Flower para inspeccion operativa de Celery

## 3. Topologia logica de despliegue

### 3.1 Frontend

Responsabilidades:

- servir la interfaz web por rol
- consumir la API REST del backend
- representar mapas, formularios, listados y vistas operativas

### 3.2 Backend

Responsabilidades:

- exponer la API del sistema
- aplicar reglas de negocio
- autenticar y autorizar usuarios
- generar facturas PDF
- orquestar tareas asincronas

### 3.3 Base de datos

Responsabilidades:

- persistir entidades de negocio
- soportar datos geograficos
- mantener relaciones y restricciones

### 3.4 Redis

Responsabilidades:

- broker de Celery
- cola de tareas y mensajes

### 3.5 Celery Worker y Celery Beat

Responsabilidades:

- autoestimacion de solicitudes expiradas
- envio de correos asincronos
- tareas programadas relacionadas con operacion

### 3.6 Flower

Responsabilidades:

- inspeccion del estado de tareas Celery
- apoyo a diagnostico durante desarrollo o demo

## 4. Entornos contemplados

### 4.1 Entorno local de desarrollo

Es el entorno principal del proyecto.
Se levanta con Docker Compose y permite:

- desarrollar backend y frontend
- probar integraciones
- cargar fixtures
- ejecutar tests
- validar flujos end-to-end

### 4.2 Entorno de demostracion o preentrega

Puede reutilizar la misma arquitectura general, endureciendo:

- variables de entorno
- credenciales reales
- politicas de logs
- datos de demo controlados

### 4.3 Entorno academico de defensa

En un contexto de TFG, la prioridad suele ser garantizar:

- facilidad de arranque
- consistencia de datos de demo
- estabilidad visual
- acceso rapido a modulos clave

Por ello, para defensa conviene disponer de:

- una base de datos ya poblada
- usuarios demo conocidos
- servicios levantados antes de la presentacion
- ventas de ejemplo verificadas y facturas PDF descargables bajo demanda

## 5. Variables de entorno y configuracion

## 5.1 Variables de base de datos

- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

## 5.2 Variables de Celery y Redis

- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## 5.3 Variables de Google

- `GOOGLE_MAPS_API_KEY`

Notas operativas:

- se usa para geocodificacion de clientes
- se usa para optimizacion de paradas en `generate-week`
- se usa para exportar navegacion externa desde ejecucion de ruta
- si la clave falta o falla, la operacion principal sigue disponible con fallback secuencial

## 5.4 Variables de Gmail API

- `GMAIL_FROM`
- `GMAIL_CLIENT_SECRET_JSON`
- `GMAIL_TOKEN_JSON`

## 5.5 Recomendaciones operativas sobre configuracion

- no versionar secretos reales
- mantener los JSON OAuth en una sola linea dentro de `.env`
- diferenciar credenciales de desarrollo, demo y produccion
- validar siempre que la configuracion de Gmail y Google no bloquee el flujo principal si falla

## 6. Puesta en marcha recomendada

## 6.1 Arranque inicial

```bash
docker-compose up --build
```

## 6.2 Migraciones

```bash
python manage.py migrate
```

## 6.3 Carga de fixtures

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

## 6.4 Servicios esperados

- backend disponible
- frontend disponible
- PostgreSQL accesible
- Redis accesible
- Celery Worker levantado
- Celery Beat levantado

## 6.5 Verificaciones minimas tras arranque

- acceso a `/admin/`
- acceso a `/docs/`
- login owner correcto
- dashboard visible
- listado de rutas accesible
- `operational-overview` accesible para al menos una ruta
- venta de prueba visible
- factura PDF descargable

## 7. Operacion funcional diaria

Desde la perspectiva de negocio, la operacion cotidiana se apoya en:

- consulta de dashboard
- generacion semanal de rutas
- supervision de solicitudes de recogida
- ejecucion de jornadas
- control de tramos y retornos operativos al hub cuando la capacidad lo exige
- medicion y cierre de recogidas
- registro de ventas y descarga de facturas
- revision de estadisticas

En este punto conviene remarcar que la descarga de facturas no depende de ficheros previamente almacenados. Si los datos fiscales, comprador o venta cambian, el documento se genera con los datos vigentes.

Desde la perspectiva tecnica, esto implica revisar:

- estado de backend
- estado de Celery
- estado de la base de datos
- disponibilidad de integraciones opcionales

## 8. Observabilidad y diagnostico

### 8.1 Logging

El proyecto utiliza logging para dejar trazabilidad sobre:

- errores de validacion funcional
- tareas Celery
- integraciones externas
- generacion de rutas
- envio de correos

### 8.2 Flower

Flower permite revisar:

- tareas recibidas
- tareas completadas
- retries
- errores de tareas asincronas

### 8.3 Swagger y schema

La documentacion OpenAPI permite diagnosticar:

- endpoints existentes
- payloads esperados
- comportamiento general de la API

## 9. Operacion sobre datos de demo

Para una demo consistente se recomienda:

- no mezclar datos reales con datos de TFG
- mantener usuarios demo con roles claros
- conservar una secuencia de facturas de ejemplo
- revisar que existan compradores y ventas de muestra
- asegurar que rutas y recogidas recientes sigan presentes

## 10. Backup y recuperacion

## 10.1 Recomendaciones de backup

- copia periodica de la base de datos PostgreSQL
- custodia separada de los medios de backup
- copia del directorio de media si se utilizan ficheros persistidos para imagenes u otros adjuntos
- copia controlada de `.env` sin exponer secretos en repositorios

## 10.2 Recuperacion

Ante una incidencia grave, la recuperacion minima deberia contemplar:

1. restaurar base de datos
2. restaurar configuracion de entorno
3. restaurar media persistida si aplica
4. verificar login, API, panel y facturas

Las facturas de venta no requieren restaurar binarios PDF historicos en el flujo actual, porque se reconstruyen en cada descarga a partir de `Sale`, `Buyer` y `CompanySettings`.

## 11. Riesgos operativos principales

- credenciales OAuth de Gmail revocadas o caducadas
- API key de Google no valida o sin permisos
- datos geograficos incompletos que degradan la planificacion
- base de datos vacia o sin fixtures tras un `flush`
- diferencias entre entorno Windows host y contenedores Docker
- PDFs no descargables si faltan dependencias del sistema para WeasyPrint

## 11.1 Dependencias externas y degradacion

Las integraciones externas aportan valor, pero tambien requieren una estrategia de degradacion:

- si Google Maps no esta configurado, la generacion de rutas mantiene el orden base
- si Gmail API falla, la tarea deja trazabilidad en logs y no bloquea la operacion principal
- si WeasyPrint o sus dependencias del sistema fallan, la venta sigue existiendo aunque la descarga del PDF devuelva error
- si Redis o Celery no estan disponibles, los flujos sincronos pueden funcionar, pero se pierden automatismos de autoestimacion y notificacion

Esta separacion entre flujo principal y servicios auxiliares es importante para operar el sistema con estabilidad durante desarrollo, demo o defensa.

## 12. Recomendaciones para defensa del TFG

Antes de una presentacion o reunion de revision se recomienda:

- levantar todos los servicios con antelacion
- comprobar login del owner
- validar rutas, recogidas, ventas y stats
- revisar que existan registros recientes y facturas descargables
- desactivar o controlar datos inestables que puedan romper una demo
- preparar una narrativa clara del flujo:
  - configuracion
  - generacion semanal
  - ejecucion diaria
  - medicion
  - venta
  - estadisticas

## 13. Checklist operativa minima

- backend arriba
- frontend arriba
- PostgreSQL arriba
- Redis arriba
- Celery Worker arriba
- Celery Beat arriba
- variables de entorno cargadas
- migraciones aplicadas
- fixtures presentes
- login owner correcto
- PDF de venta comprobado
- ruta operativa de ejemplo accesible

## 14. Relacion con el resto de documentos

Para ampliar este documento conviene consultar:

- `README.md`
- `docs/INDICE_DOCUMENTACION.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/API.md`
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
- `docs/PLANIFICACION_Y_COSTES.md`
- `docs/TESTING.md`

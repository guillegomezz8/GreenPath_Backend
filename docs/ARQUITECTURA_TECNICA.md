# Arquitectura Tecnica del Proyecto

## 1. Stack

- Backend: Django + Django REST Framework
- Base de datos: PostgreSQL + PostGIS
- Cola asincrona: Celery
- Broker/Backend tareas: Redis (segun despliegue del proyecto)
- Frontend: React + Vite + Tailwind + componentes UI propios
- Contenedores: Docker Compose

## 2. Estructura backend (alto nivel)

- `apps/base`
  - enums, literals, permisos, utilidades comunes.
- `apps/user`
  - usuarios, clientes, trabajadores, empresas.
- `apps/route`
  - rutas plantilla, dias operativos, paradas.
- `apps/collection`
  - recogidas y solicitudes de recogida.
- `apps/truck`
  - flota y asignacion de conductores.

## 3. Modelado operativo clave

- `Route`: plantilla de ruta.
- `RouteZoneDay`: zonas asociadas a dia de semana.
- `RouteDay`: ruta diaria generada.
- `RouteDayClient`: parada de cliente en ruta diaria.
- `CollectionRequest`: solicitud de litros para parada.
- `Collection`: recogida ejecutada.
- `CompanyHub`: origen logico de optimizacion.

## 4. Geoespacial

- `Zone` usa `PolygonField`.
- `Client` usa `PointField`.
- Seleccion de clientes para ruta diaria por pertenencia espacial (`within`).
- Poligonos definidos desde frontend de zonas.

## 5. Generacion semanal y optimizacion

La accion `POST /routes/{route_id}/generate-week/`:

1. Crea/actualiza `RouteDay`.
2. Genera `RouteDayClient` por zonas/frecuencia.
3. Optimiza orden de paradas con Google Directions (`optimize:true`).
4. Crea/actualiza `CollectionRequest`.
5. Agenda Celery para autoestimacion en `expires_at`.

## 6. Ejecucion operativa de ruta

- Inicio de dia: `start_route_day`.
- Registro de parada: `complete_stop`.
- Cierre de dia: `finish_route_day`.
  - con pendientes exige decision (`PARTIAL` o `CANCELED`).

## 7. Solicitudes y trazabilidad

`CollectionRequest` guarda:

- datos de plan (`container_type`, `container_number`, `estimated_liters`).
- resultado (`final_liters`, `final_source`).
- trazabilidad:
  - `answered_by`, `answered_at`
  - `manual_by`, `manual_at`
- task scheduling:
  - `auto_estimate_task_id`
  - `auto_estimate_scheduled_at`

## 8. Seguridad y permisos

- Seguridad por autenticacion JWT.
- Permisos por rol (`owner`, `worker`, `client`).
- Restriccion por empresa en querysets y acciones criticas.
- Nuevo permiso dedicado para generacion de ruta semanal.

## 9. Frontend y modularidad

- Paginas por dominio (`clients`, `workers`, `routes`, `collections`, etc).
- Layout comun (`MainLayout`, `Sidebar`, `Topbar`).
- Navegacion por rol desde sidebar.
- Utilidades comunes de estado/errores en `components/Utils`.

## 10. Observabilidad

- Logging unificado con formato:
  - `logging.info/error/warning([archivo - funcion] mensaje)`
- Uso de literales centralizados para mensajes API.

## 11. Despliegue local

Recomendado:

1. Levantar backend y frontend con Docker Compose.
2. Cargar fixtures.
3. Crear semana operativa desde detalle de ruta.
4. Ejecutar flujo de parada y validacion de solicitudes.

## 12. Riesgos tecnicos conocidos

- Concurrencia extrema en regeneraciones semanales: mitigada parcialmente, escalable con lock distribuido.
- Integraciones externas (Google Directions, correo): requieren credenciales y monitorizacion.
- Calidad de datos geograficos: coordenadas invalidas afectan inclusion de clientes.

## 13. Recomendaciones inmediatas

- Añadir tests E2E de flujo:
  - generar semana -> ejecutar paradas -> cerrar route day.
- Auditar todos los `get_queryset` para cubrir rol client sin errores.
- Añadir dashboard especifico de salud de tareas Celery.


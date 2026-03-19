# Arquitectura Tecnica del Proyecto

## 1. Stack

- Backend: Django + Django REST Framework
- Base de datos: PostgreSQL + PostGIS
- Cola asincrona: Celery
- Broker/Backend de tareas: Redis
- Frontend: React + Vite + Tailwind + componentes UI propios
- PDF de facturas: WeasyPrint + plantilla HTML/CSS
- Contenedores: Docker Compose

## 2. Estructura backend (alto nivel)

- `apps/base`
  - enums, literals, permisos, utilidades comunes
- `apps/user`
  - usuarios, clientes y trabajadores
- `apps/company`
  - empresa, hub y configuracion global (`CompanySettings`)
- `apps/sale`
  - compradores, ventas, facturas PDF y resumen economico
- `apps/route`
  - rutas plantilla, dias operativos y paradas
- `apps/collection`
  - recogidas y solicitudes de recogida
- `apps/truck`
  - flota y asignacion de conductores
- `apps/zone`
  - zonas geograficas de recogida

## 3. Modelado operativo clave

- `Route`: plantilla de ruta
- `RouteZoneDay`: zonas asociadas a un dia de semana
- `RouteDay`: ruta diaria generada
- `RouteDayClient`: parada de cliente en una ruta diaria
- `CollectionRequest`: solicitud de litros previa a la recogida
- `Collection`: recogida ejecutada y liquidable
- `Buyer`: comprador interno para el modulo de ventas
- `Sale`: venta con datos fiscales, importes calculados y PDF asociado
- `CompanyHub`: origen logico de optimizacion
- `CompanySettings`: configuracion global por empresa para precio por litro, hub y datos fiscales de facturacion

## 4. Geoespacial

- `Zone` usa `PolygonField`
- `Client` usa `PointField`
- La seleccion de clientes para una ruta diaria usa pertenencia espacial (`within`)
- El frontend define y edita poligonos desde mapa

## 5. Generacion semanal y optimizacion

La accion `POST /routes/{route_id}/generate-week/`:

1. Crea o actualiza `RouteDay`
2. Si `regenerate=true`, valida antes que toda la semana siga siendo editable y sin ejecucion previa
3. Preserva cualquier `RouteDay` que ya no sea editable
4. Genera `RouteDayClient` por zonas y frecuencia
5. Respeta `max_clients_per_day` y `daily_capacity_liters` de forma estricta
6. Optimiza el orden con Google Directions (`optimize:true`)
7. Crea o actualiza `CollectionRequest`
8. Agenda Celery para autoestimacion en `expires_at`

## 6. Ejecucion operativa de ruta

- Inicio de dia: `start_route_day`
- Registro de parada: `complete_stop`
- Cierre de dia: `finish_route_day`
  - con pendientes exige decision (`PARTIAL` o `CANCELED`)
  - sin pendientes cierra como `COMPLETED`, aunque existan paradas canceladas

## 6.1 Configuracion global de empresa

- Endpoint: `GET/PUT /companies/settings/`
- Modelo: `CompanySettings` (one-to-one con `Company`)
- Uso actual:
  - `default_price_per_liter`
  - hub de empresa
  - datos fiscales y bancarios para facturas PDF
- Aplicacion:
  - creacion manual de `Collection`
  - registro de parada desde `RouteDay`
  - emision y regeneracion de facturas de venta

## 6.2 Ventas y facturacion

- Modelos:
  - `Buyer`
  - `Sale`
- Endpoints:
  - `/buyers/`
  - `/sales/`
  - `/sales/{id}/invoice/download/`
  - `/sales/{id}/invoice/regenerate/`
  - `/sales/economic-summary/`
- Reglas:
  - acceso solo `owner`
  - `invoice_number` manual y unico por empresa
  - `invoice_date` como unica fecha funcional visible
  - `sale_date` se sincroniza internamente con `invoice_date`
  - `subtotal`, `tax_amount` y `total` se recalculan en backend
  - el PDF se genera con WeasyPrint usando `templates/sale/invoice.html`

## 7. Solicitudes y trazabilidad

`CollectionRequest` guarda:

- datos de plan (`container_type`, `container_number`, `estimated_liters`)
- resultado (`final_liters`, `final_source`)
- trazabilidad:
  - `answered_by`, `answered_at`
  - `manual_by`, `manual_at`
- scheduling:
  - `auto_estimate_task_id`
  - `auto_estimate_scheduled_at`

## 8. Seguridad y permisos

- Seguridad por autenticacion JWT
- Permisos por rol (`owner`, `worker`, `client`)
- Restriccion por empresa en querysets y acciones criticas
- Permiso dedicado para generacion de ruta semanal
- Bloque de compradores, ventas, facturas y configuracion fiscal restringido a `owner`

## 9. Frontend y modularidad

- Paginas por dominio (`clients`, `workers`, `routes`, `collections`, `buyers`, `sales`, `settings`, `stats`)
- Layout comun (`MainLayout`, `Sidebar`, `Topbar`)
- Navegacion por rol desde sidebar
- Utilidades comunes de estado y errores en `components/Utils`
- En rutas:
  - `RouteDetail` prioriza planificacion y consulta semanal
  - `RouteExecution` concentra la operativa diaria con mapa, acciones y modales responsive
  - `GenerateWeekDialog` se comparte entre listado y detalle
- En negocio economico:
  - `BuyersList`, `BuyerCreate`, `BuyerEdit`, `BuyerDetail`
  - `SalesList`, `SaleCreate`, `SaleEdit`, `SaleDetail`
  - `CompanySettingsPage` permite ajustar precio global, datos fiscales y hub
  - `Stats` consume resumen economico combinado de recogidas y ventas

## 10. Observabilidad

- Logging unificado con formato:
  - `logging.info/error/warning([archivo - funcion] mensaje)`
- Uso de literales centralizados para respuestas y mensajes API

## 11. Despliegue local

Recomendado:

1. Levantar backend y frontend con Docker Compose
2. Cargar fixtures, incluyendo:
   - `apps/user/fixtures/11-company-settings.json`
   - `apps/user/fixtures/12-buyers.json`
   - `apps/user/fixtures/13-sales.json`
3. Crear semana operativa desde detalle de ruta
4. Ejecutar flujo de parada y validacion de solicitudes
5. Revisar ventas y facturas desde el modulo owner

## 12. Riesgos tecnicos conocidos

- Concurrencia extrema en regeneraciones semanales: mitigada parcialmente, escalable con lock distribuido
- Integraciones externas (Google Directions, correo): requieren credenciales y monitorizacion
- WeasyPrint: requiere dependencias del sistema presentes en la imagen Docker
- Calidad de datos geograficos: coordenadas invalidas afectan inclusion de clientes

## 13. Recomendaciones inmediatas

- Anadir tests E2E de flujo:
  - generar semana -> ejecutar paradas -> cerrar route day
  - crear venta -> regenerar factura -> descargar PDF
- Auditar todos los `get_queryset` para cubrir rol client sin errores
- Anadir dashboard especifico de salud de tareas Celery

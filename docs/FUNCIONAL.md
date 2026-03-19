# Documento Funcional GreenPath

## 1. Vision del producto

GreenPath es una plataforma para gestionar la recogida de aceite usado desde clientes hasta la nave (hub) de la empresa operadora.
El sistema cubre:

- Planificacion de rutas por zonas y dias.
- Generacion operativa semanal de paradas.
- Ejecucion diaria de ruta (inicio, registro de parada, cierre).
- Gestion de solicitudes de litros al cliente (`CollectionRequest`).
- Registro y cierre economico de recogidas (`Collection`).
- Gestion interna de compradores (`Buyer`).
- Registro de ventas (`Sale`) y facturas PDF asociadas.
- Configuracion global por empresa para valores operativos y economicos.
- Gestion de flota, trabajadores, clientes y zonas.

## 2. Roles de usuario

### 2.1 Owner

- Gestion completa de entidades (clientes, trabajadores, camiones, rutas, zonas, recogidas).
- Gestion de compradores, ventas y facturas.
- Generacion de semana operativa.
- Cierre manual de solicitudes de litros cuando sea necesario.
- Control de asignaciones de camiones/conductores.
- Configuracion fiscal y bancaria de la empresa.

### 2.2 Worker

- Operacion diaria de rutas y paradas.
- Registro de recogidas en parada (fase calle).
- Consulta de clientes/rutas/recogidas dentro de su empresa.
- Carga manual de litros en solicitudes cuando aplica.

### 2.3 Client

- Consulta de sus solicitudes de recogida.
- Respuesta de litros antes de expiracion.
- Consulta de su historial de recogidas.

## 3. Modulos funcionales

## 3.1 Clientes

- Alta, edicion, baja logica.
- Datos de contacto y frecuencia de recogida.
- Historial consolidado de recogidas por cliente.
- Estadisticas: confirmadas, pendientes, canceladas, litros netos, total pagado.

## 3.2 Trabajadores

- Alta, edicion, baja logica.
- Activacion/desactivacion.
- Perfil y datos operativos.
- Relacion con empresa.

## 3.3 Camiones

- Alta/edicion/baja logica de vehiculos.
- Estado operativo (activo, en servicio, mantenimiento, etc).
- Asignacion de conductor con reglas de empresa.

## 3.4 Zonas de recogida

- Definicion geoespacial de poligonos.
- Edicion visual en mapa.
- Uso en configuracion semanal de rutas.

## 3.5 Rutas

- Ruta plantilla con dias de operacion y trabajadores.
- Configuracion de zonas por dia (`RouteZoneDay`).
- Generacion semanal operativa (`RouteDay` + `RouteDayClient`).
- Vista operativa por dia con estado, paradas y accion de ejecucion.

## 3.6 Recogidas

- Registro de parada con envases y notas.
- Estados: pendiente de medicion, confirmada, cancelada.
- Medicion y ajustes posteriores en nave.
- Impacto economico (litros netos y total).
- Precio por litro precargado desde la configuracion global de empresa.

## 3.7 Compradores

- Modulo interno solo para owner.
- Alta, edicion, detalle y listado.
- Datos fiscales completos:
  - razon social
  - CIF/NIF
  - direccion fiscal
  - codigo postal, ciudad, provincia y pais
  - email, telefono y contacto
  - observaciones
- Sin acceso a plataforma para los compradores.

## 3.8 Ventas

- Modulo interno solo para owner.
- Alta, edicion, detalle y listado.
- Numero de factura manual.
- Una sola fecha visible y funcional: `invoice_date`.
- Calculo automatico de base imponible, IVA y total.
- PDF asociado descargable y regenerable.

## 3.9 Facturacion de venta

- Cada venta queda vinculada a su PDF.
- El PDF usa datos fiscales configurables de la empresa.
- El comprador aporta automaticamente los datos del destinatario.
- La plantilla esta pensada para exportacion en A4 y regeneracion desde backend.

## 3.10 Configuracion de empresa

- Parametros globales por empresa.
- Actualmente incluye:
  - `default_price_per_liter`
  - hub de empresa
  - razon social
  - CIF
  - direccion fiscal
  - codigo postal, ciudad, provincia y pais
  - telefono
  - email
  - cuenta bancaria
  - Codigo LER
  - pie de factura
- Editable por owner desde pantalla dedicada de configuracion.

## 3.11 Solicitudes de recogida (`CollectionRequest`)

- Se crean al generar paradas semanales.
- Tienen fecha limite de respuesta (`expires_at`).
- Pueden quedar en:
  - `PENDING`
  - `AUTO_ESTIMATED`
  - `ANSWERED`
  - `MANUAL`
- Se programa tarea Celery de autoestimacion.

## 3.12 Dashboard y estadisticas

- KPIs de operacion.
- Actividad reciente.
- Vista adaptada por rol (owner/worker vs client).
- Bloque economico con:
  - total invertido en recogidas
  - total ingresado en ventas
  - beneficio neto
  - volumen comprado vs vendido

## 4. Flujo funcional principal

## 4.1 Configuracion inicial

1. Crear empresa, workers, clientes y zonas.
2. Crear ruta plantilla con rango semanal.
3. Configurar zonas por dia en la ruta.
4. Definir hub de empresa.
5. Definir precio global por litro en configuracion de empresa.
6. Completar datos fiscales y bancarios para facturacion.

## 4.2 Generacion semanal

1. Usuario owner abre listado o detalle de ruta.
2. Ejecuta `Generar semana` con fecha de inicio y capacidad.
3. Backend crea/actualiza `RouteDay`.
4. Backend calcula clientes por zona y frecuencia.
5. Se crean `RouteDayClient` con orden inicial.
6. Se optimiza orden con Google Directions.
7. Se crea `CollectionRequest` por parada.
8. Se agenda autoestimacion y notificacion.
9. El modal de generacion se presenta con layout responsive y comportamiento consistente en listado y detalle.

## 4.3 Ejecucion diaria de ruta

1. Usuario owner/worker entra en `Realizar ruta`.
2. Iniciar `RouteDay`.
3. Seleccionar parada pendiente en dropdown.
4. Registrar parada con tipo y numero de envase.
5. Repetir hasta fin del dia.
6. Finalizar `RouteDay`:
   - si no quedan pendientes -> cierre normal (`COMPLETED`).
   - si quedan pendientes -> modal de decision:
     - `PARTIAL`
     - `CANCELED`
7. UX responsive:
   - `Detalle de ruta` queda como pantalla de planificacion y consulta.
   - `Realizar ruta` concentra mapa, jornada activa y parada pendiente en una sola vista.
   - en movil, el panel operativo se apila bajo el mapa y las acciones criticas pasan a boton ancho completo.
   - los modales de cierre y registro de parada usan scroll interno y CTA apiladas en pantallas pequenas.

## 4.4 Cierre de litros

- En parada se registra recogida fisica.
- La medicion fina y descuentos se aplican despues en fase nave.
- El impacto economico se calcula con litros netos.
- El precio por litro nace con el valor global de empresa, aunque se puede editar por recogida.

## 4.5 Flujo de ventas y facturacion

1. Owner crea o selecciona un comprador interno.
2. Registra una venta con numero de factura manual.
3. Introduce la fecha de factura (`invoice_date`) y los datos economicos de la operacion.
4. Backend calcula subtotal, IVA y total.
5. Se genera o regenera el PDF de factura.
6. La venta pasa a formar parte del resumen economico global.

## 4.6 Interaccion cliente con solicitudes

1. Cliente entra a `Mis solicitudes`.
2. Visualiza solicitudes abiertas y limite de respuesta.
3. Introduce litros finales.
4. Backend valida expiracion y estado.
5. Solicitud pasa a `ANSWERED`.

## 5. Reglas de negocio clave

- La generacion semanal es idempotente.
- `regenerate` solo tiene sentido cuando ya existen paradas en la semana.
- `regenerate=true` queda bloqueado si la semana contiene dias que ya no son editables.
- Los dias ya operados se preservan cuando se vuelve a generar la semana sin `regenerate`.
- La capacidad diaria se aplica de forma estricta desde la primera parada.
- `expires_at` se fija en `inicio_route_day - 36h`.
- La solicitud expirada no admite respuesta del cliente.
- Owner/Worker pueden resolver manualmente solicitudes.
- La ruta diaria solo se puede iniciar desde estados permitidos.
- La finalizacion con pendientes requiere decision explicita (`PARTIAL` o `CANCELED`).
- El orden de paradas puede forzarse al registrar (flag `force`).
- Si una ruta diaria ya no tiene pendientes, las paradas canceladas no impiden cerrar como `COMPLETED`.
- Si no se informa `price_per_liter` al crear una recogida manual, se toma el valor global de empresa.
- Las ventas computan como ingreso y las recogidas confirmadas como coste.
- El beneficio neto se calcula como `ventas - recogidas confirmadas`.
- El numero de factura de venta es manual y debe ser unico dentro de la empresa.

## 6. Estados funcionales

## 6.1 RouteDay

- `PLANNED`
- `IN_PROGRESS`
- `COMPLETED`
- `PARTIAL`
- `CANCELED`

## 6.2 CollectionRequest

- `PENDING`
- `AUTO_ESTIMATED`
- `ANSWERED`
- `MANUAL`

## 6.3 Collection

- `PENDING_MEASUREMENT`
- `CONFIRMED`
- `CANCELED`

## 7. Seguridad funcional

- Aislamiento por empresa en consultas operativas.
- Restricciones por rol en acciones sensibles:
  - creacion/edicion/borrado de recursos maestros.
  - cierre manual de solicitudes.
  - generacion de semana.
- Trazabilidad de quien responde/manualmente actualiza solicitud.

## 8. UX funcional esperada

- Owner/Worker:
  - menu completo de gestion y operacion.
  - modulos adicionales de compradores, ventas, configuracion fiscal y estadisticas economicas.
  - dashboard operativo.
  - detalle de ruta orientado a planificacion y seguimiento semanal.
  - pantalla `Realizar ruta` orientada a ejecucion diaria con mapa y control de parada activa.
- Client:
  - menu reducido: dashboard, solicitudes y recogidas.
  - foco en responder litros y consultar historico.
- Mobile-first:
  - prioridad de legibilidad en acciones de ruta.
  - tablas operativas con alternativa en tarjetas para evitar perdida de usabilidad.

## 9. Operacion y mantenimiento

- Tareas periodicas en Celery para solicitudes.
- Logs normalizados por archivo/funcion.
- Generacion semanal protegida frente a colisiones basicas.
- Documentacion tecnica en:
  - `docs/API.md`
  - `docs/ROUTE_FLOW.md`

## 10. Roadmap funcional sugerido

- Confirmar politica final para autoestimacion en lotes masivos.
- Incorporar bloqueo distribuido estricto para regeneraciones concurrentes extremas.
- Mejorar panel cliente con timeline de solicitud -> recogida -> confirmacion.
- Anadir trazabilidad de auditoria exportable en CSV/PDF.

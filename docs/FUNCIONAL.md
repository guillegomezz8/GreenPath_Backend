# Documento Funcional GreenPath

## 1. Vision del producto

GreenPath es una plataforma para gestionar la recogida de aceite usado desde clientes hasta la nave (hub) de la empresa operadora.
El sistema cubre:

- Planificacion de rutas por zonas y dias.
- Generacion operativa semanal de paradas.
- Ejecucion diaria de ruta (inicio, registro de parada, cierre).
- Gestion de solicitudes de litros al cliente (`CollectionRequest`).
- Registro y cierre economico de recogidas (`Collection`).
- Gestion de flota, trabajadores, clientes y zonas.

## 2. Roles de usuario

### 2.1 Owner

- Gestion completa de entidades (clientes, trabajadores, camiones, rutas, zonas, recogidas).
- Generacion de semana operativa.
- Cierre manual de solicitudes de litros cuando sea necesario.
- Control de asignaciones de camiones/conductores.

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

## 3.7 Solicitudes de recogida (`CollectionRequest`)

- Se crean al generar paradas semanales.
- Tienen fecha limite de respuesta (`expires_at`).
- Pueden quedar en:
  - `PENDING`
  - `AUTO_ESTIMATED`
  - `ANSWERED`
  - `MANUAL`
- Se programa tarea Celery de autoestimacion.

## 3.8 Dashboard y estadisticas

- KPIs de operacion.
- Actividad reciente.
- Vista adaptada por rol (owner/worker vs client).

## 4. Flujo funcional principal

## 4.1 Configuracion inicial

1. Crear empresa, workers, clientes y zonas.
2. Crear ruta plantilla con rango semanal.
3. Configurar zonas por dia en la ruta.
4. Definir hub de empresa.

## 4.2 Generacion semanal

1. Usuario owner/worker abre detalle de ruta.
2. Ejecuta `Generar semana` con fecha de inicio y capacidad.
3. Backend crea/actualiza `RouteDay`.
4. Backend calcula clientes por zona y frecuencia.
5. Se crean `RouteDayClient` con orden inicial.
6. Se optimiza orden con Google Directions.
7. Se crea `CollectionRequest` por parada.
8. Se agenda autoestimacion y notificacion.

## 4.3 Ejecucion diaria de ruta

1. Iniciar `RouteDay`.
2. Seleccionar parada pendiente en dropdown.
3. Registrar parada con tipo y numero de envase.
4. Repetir hasta fin del dia.
5. Finalizar `RouteDay`:
   - si no quedan pendientes -> cierre normal (`COMPLETED` o `PARTIAL` segun canceladas).
   - si quedan pendientes -> modal de decision:
     - `PARTIAL`
     - `CANCELED`
6. UX responsive:
   - en desktop se usa tabla de paradas y acciones por fila.
   - en movil se usa vista en tarjetas por parada para operar sin scroll horizontal.
   - acciones criticas (`Google`, `Iniciar`, `Finalizar`, `Recoger parada`) adaptadas a boton ancho completo en pantallas pequenas.

## 4.4 Cierre de litros

- En parada se registra recogida fisica.
- La medicion fina y descuentos se aplican despues en fase nave.
- El impacto economico se calcula con litros netos.

## 4.5 Interaccion cliente con solicitudes

1. Cliente entra a `Mis solicitudes`.
2. Visualiza solicitudes abiertas y limite de respuesta.
3. Introduce litros finales.
4. Backend valida expiracion y estado.
5. Solicitud pasa a `ANSWERED`.

## 5. Reglas de negocio clave

- La generacion semanal es idempotente.
- `regenerate` solo tiene sentido cuando ya existen paradas en la semana.
- `expires_at` se fija en `inicio_route_day - 36h`.
- La solicitud expirada no admite respuesta del cliente.
- Owner/Worker pueden resolver manualmente solicitudes.
- La ruta diaria solo se puede iniciar desde estados permitidos.
- La finalizacion con pendientes requiere decision explicita (`PARTIAL` o `CANCELED`).
- El orden de paradas puede forzarse al registrar (flag `force`).

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
  - dashboard operativo.
  - detalle de ruta orientado a ejecucion con resumen, filtros por estado y progreso diario.
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

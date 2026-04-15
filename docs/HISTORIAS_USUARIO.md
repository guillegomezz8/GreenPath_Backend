# Historias de Usuario GreenPath

Fecha de revision: 2026-04-14

## 1. Convenciones

- Prioridad:
  - `P0`: imprescindible para operar.
  - `P1`: muy importante para productividad/escala.
  - `P2`: mejora de calidad/experiencia.
- Roles:
  - `Owner`
  - `Worker`
  - `Client`

## 2. Historias Owner

### US-OWN-001 (P0) Crear y mantener rutas plantilla

Como Owner quiero crear/editar rutas plantilla con un trabajador asignado y rango operativo para planificar semanas de trabajo.

Criterios de aceptacion:
1. Puedo crear ruta con nombre, fechas, `week_start`, `week_end` y un trabajador asignado.
2. Puedo editar una ruta existente sin perder configuracion valida.
3. Si faltan datos obligatorios, el sistema bloquea guardado y muestra error.

### US-OWN-002 (P0) Configurar zonas por dia operativo

Como Owner quiero asignar zonas por dia para que la generacion semanal use la segmentacion correcta.

Criterios de aceptacion:
1. Solo se muestran dias del rango operativo configurado (`week_start`-`week_end`).
2. Puedo seleccionar multiples zonas por dia.
3. Al guardar, la configuracion queda persistida en `RouteZoneDay`.

### US-OWN-003 (P0) Generar semana operativa

Como Owner quiero generar una semana de ruta para obtener `RouteDay` y paradas operativas.

Criterios de aceptacion:
1. Puedo generar por `week_start_date`.
2. Puedo decidir regenerar cuando ya hay paradas.
3. Se crean/actualizan `RouteDay`, `RouteDayClient` y `CollectionRequest`.

### US-OWN-004 (P1) Supervisar ejecucion por estado

Como Owner quiero ver estados de `RouteDay` para detectar rapidamente bloqueos operativos.

Criterios de aceptacion:
1. El detalle de ruta muestra resumen de dias y paradas.
2. Existen filtros por estado de dia (`PLANNED`, `IN_PROGRESS`, `PARTIAL`, `COMPLETED`, `CANCELED`).
3. Puedo expandir/colapsar dias en bloque.

### US-OWN-005 (P1) Navegacion operativa y cierre controlado

Como Owner quiero iniciar/finalizar dias con reglas claras para mantener consistencia de operacion.

Criterios de aceptacion:
1. `start` solo se permite en estados validos.
2. Si hay paradas pendientes al finalizar, se exige decision (`PARTIAL` o `CANCELED`).
3. Puedo abrir enlace de navegacion Google por dia.

### US-OWN-005G (P1) Entender retornos al hub por capacidad

Como Owner quiero que la operativa me indique cuando una jornada requiere volver a nave para supervisar mejor la ruta real.

Criterios de aceptacion:
1. El sistema calcula tramos operativos dentro de un `RouteDay`.
2. El resumen operativo muestra numero de tramos y retornos previstos.
3. La navegacion de Google incorpora el hub entre segmentos cuando la capacidad lo exige.

### US-OWN-005B (P1) Configurar precio global de empresa

Como Owner quiero definir un precio global por litro para que las recogidas nazcan con un valor economico coherente.

Criterios de aceptacion:
1. Existe una pantalla de configuracion accesible solo para owner.
2. Puedo guardar un `default_price_per_liter` por empresa.
3. Las nuevas recogidas toman ese valor por defecto sin impedir ajuste manual posterior.

### US-OWN-005C (P0) Gestionar compradores internos

Como Owner quiero mantener una cartera interna de compradores para reutilizar sus datos fiscales al crear ventas.

Criterios de aceptacion:
1. Puedo crear, editar, listar y consultar compradores.
2. Los compradores guardan razon social, CIF, direccion fiscal y datos de contacto.
3. Los compradores no tienen acceso a la plataforma.

### US-OWN-005D (P0) Registrar ventas con factura

Como Owner quiero registrar ventas con numero de factura manual para controlar ingresos reales del negocio.

Criterios de aceptacion:
1. Puedo crear una venta seleccionando comprador y fecha de factura.
2. El sistema calcula base imponible, IVA y total.
3. Puedo descargar y regenerar el PDF de factura de esa venta.

### US-OWN-005E (P1) Configurar datos fiscales de empresa

Como Owner quiero editar los datos fiscales y bancarios de mi empresa sin tocar codigo.

Criterios de aceptacion:
1. Existe una pantalla de configuracion solo para owner.
2. Puedo guardar razon social, CIF, direccion fiscal, cuenta bancaria y Codigo LER.
3. Las facturas nuevas reutilizan esos datos automaticamente.

### US-OWN-005F (P1) Ver beneficio neto real

Como Owner quiero ver costes, ingresos y beneficio neto para entender la rentabilidad real del negocio.

Criterios de aceptacion:
1. Las recogidas confirmadas computan como coste.
2. Las ventas computan como ingreso.
3. Las estadisticas muestran balance neto y evolucion mensual.

## 3. Historias Worker

### US-WRK-001 (P0) Ver solo rutas asignadas

Como Worker quiero ver rutas operativas relevantes para mi trabajo diario.

Criterios de aceptacion:
1. El listado de rutas respeta permisos por rol/empresa.
2. Puedo entrar al detalle operativo de una ruta asignada.
3. No puedo realizar acciones de administracion de Owner.

### US-WRK-002 (P0) Operar paradas en calle

Como Worker quiero registrar paradas con datos minimos para avanzar el trabajo del dia.

Criterios de aceptacion:
1. Puedo elegir parada pendiente y registrar envases/notas.
2. Solo puedo registrar cuando el dia esta `IN_PROGRESS`.
3. El registro crea/actualiza la recogida ligada a la parada.

### US-WRK-003 (P1) Trabajo fluido en movil

Como Worker quiero ejecutar la ruta desde movil sin depender de tablas anchas.

Criterios de aceptacion:
1. En movil veo paradas en tarjetas legibles.
2. Acciones criticas (iniciar/finalizar/recoger) son accesibles en boton ancho completo.
3. No necesito scroll horizontal para operar.

### US-WRK-004 (P1) Control visual del progreso diario

Como Worker quiero ver progreso por dia para priorizar pendientes.

Criterios de aceptacion:
1. Cada `RouteDay` muestra registradas y pendientes.
2. Existe barra de progreso por dia.
3. El estado del dia es visible con badge.

### US-WRK-005 (P1) Saber en que tramo estoy trabajando

Como Worker quiero que la app me diga en que tramo estoy para entender si debo volver a nave antes de seguir recogiendo.

Criterios de aceptacion:
1. La pantalla operativa simplifica la informacion tecnica y prioriza la siguiente parada sugerida.
2. El mapa y la navegacion reflejan cuando la jornada exige retorno al hub.
3. La siguiente parada sugerida es coherente con el plan operativo interno mientras existan pendientes.

## 4. Historias Client

### US-CLI-001 (P0) Ver mis solicitudes de litros

Como Client quiero ver mis `CollectionRequest` para responder antes del limite.

Criterios de aceptacion:
1. Solo veo solicitudes propias.
2. Veo estado y `expires_at` de cada solicitud.
3. Puedo filtrar por estado.

### US-CLI-002 (P0) Responder litros

Como Client quiero responder litros finales para evitar autoestimaciones no deseadas.

Criterios de aceptacion:
1. Solo puedo responder solicitudes abiertas (`PENDING` o `AUTO_ESTIMATED`) no expiradas.
2. Al responder, estado cambia a `ANSWERED`.
3. Queda trazabilidad de respuesta.

### US-CLI-003 (P1) Consultar historial de recogidas

Como Client quiero revisar mi historico para control y conciliacion.

Criterios de aceptacion:
1. Puedo ver recogidas pasadas y sus estados.
2. Veo litros relevantes de cada recogida.
3. El listado se limita a mi empresa/perfil.

## 5. Historias de Plataforma y Calidad

### US-PLT-001 (P0) Seguridad por empresa y rol

Como sistema quiero restringir acceso por rol y empresa para proteger datos.

Criterios de aceptacion:
1. Endpoints sensibles validan empresa/rol.
2. El frontend no muestra modulos no autorizados.
3. Acceso indebido devuelve `403` o redireccion segura.

### US-PLT-002 (P1) Robustez en generacion semanal

Como sistema quiero evitar duplicidades por concurrencia en `generate-week`.

Criterios de aceptacion:
1. Existe lock por ruta+semana durante generacion.
2. Solicitudes concurrentes conflictivas no duplican paradas.
3. El proceso es idempotente con `regenerate` controlado.

### US-PLT-003 (P1) Integracion con Google con fallback

Como sistema quiero optimizar orden con Google sin romper operacion cuando falle.

Criterios de aceptacion:
1. Si Google responde, se aplica orden optimizado.
2. Si Google falla o falta API key, se mantiene orden actual.
3. El flujo de generacion no se interrumpe por este fallo.

### US-PLT-003B (P1) Alinear plan operativo y navegacion externa

Como sistema quiero que mapa operativo y enlace Google usen el mismo criterio de segmentacion para no mostrar recorridos contradictorios.

Criterios de aceptacion:
1. El backend genera un `operational_plan` reutilizable.
2. El frontend usa ese plan para resaltar tramos y parada activa.
3. La URL de Google inserta el hub entre segmentos cuando la capacidad obliga a ello.

### US-PLT-004 (P1) Programacion automatica de solicitudes

Como sistema quiero programar autoestimacion en `expires_at` para mantener continuidad operativa.

Criterios de aceptacion:
1. Se calcula `expires_at = inicio_route_day - 36h`.
2. Se agenda tarea Celery en `eta=expires_at` o inmediata si ya vencio.
3. Se evita duplicar tareas activas para la misma solicitud.

### US-PLT-005 (P2) Documentacion viva

Como equipo quiero documentacion actualizada para acelerar mantenimiento y onboarding.

Criterios de aceptacion:
1. API, flujo de rutas y pantallas reflejan estado real.
2. Existe inventario de historias de usuario con prioridad.
3. Cada revision documental relevante deja evidencia fechada.

## 6. Historias UX movil (transversal)

### US-UXM-001 (P0) Operacion de ruta sin friccion en movil

Como usuario operativo quiero completar una ruta diaria completa desde movil.

Criterios de aceptacion:
1. Puedo iniciar dia, registrar paradas y finalizar sin cambiar a desktop.
2. El detalle de parada muestra informacion minima necesaria (cliente, estado, limite, plan base).
3. Los controles criticos son visibles y tocables con una mano.
4. El usuario entiende rapidamente si esta en un tramo con retorno posterior a nave.

### US-UXM-002 (P1) Resumen rapido en pantalla pequena

Como usuario quiero entender en segundos el estado de la semana operativa.

Criterios de aceptacion:
1. Hay KPIs resumidos en la parte superior.
2. Los filtros por estado son accesibles en chips/botones compactos.
3. La jerarquia visual prioriza acciones operativas sobre informacion secundaria.

## 7. Historias Owner (ampliacion)

### US-OWN-006 (P1) Reasignar trabajador sin romper plan operativo

Como Owner quiero reasignar el trabajador de una ruta para cubrir bajas o cambios de turno.

Criterios de aceptacion:
1. Puedo editar el trabajador asignado desde formulario de ruta.
2. La ruta mantiene su configuracion de zonas y rango semanal.
3. El cambio queda reflejado en listado y detalle de ruta.

### US-OWN-007 (P1) Gestionar rutas sin trabajadores asignados

Como Owner quiero identificar rutas sin trabajadores para corregir planificacion.

Criterios de aceptacion:
1. En listado existen filtros para ver rutas sin trabajadores.
2. Se visualiza contador de rutas con/sin asignacion.
3. Puedo abrir rapidamente la ruta y editarla.

### US-OWN-008 (P1) Filtrar operativa por semana

Como Owner quiero cambiar de semana para revisar ejecucion historica o futura.

Criterios de aceptacion:
1. Puedo filtrar el detalle con `week_start_date`.
2. El sistema muestra los `RouteDay` de la semana filtrada.
3. Puedo limpiar filtro y volver a vista por defecto.

### US-OWN-009 (P1) Regenerar semana de forma segura

Como Owner quiero regenerar una semana solo cuando existe contenido previo para evitar borrados accidentales.

Criterios de aceptacion:
1. El flag de regenerar aparece solo si hay paradas existentes.
2. Si no hay paradas, se informa y se genera directo.
3. La regeneracion no deja duplicados de paradas.

### US-OWN-010 (P2) Revisar progreso de ruta diaria de un vistazo

Como Owner quiero ver porcentaje de avance diario para detectar retrasos.

Criterios de aceptacion:
1. Cada `RouteDay` muestra progreso visual.
2. Se distingue registradas, pendientes y canceladas.
3. El estado y progreso son coherentes entre si.

### US-OWN-011 (P2) Detectar dias bloqueados en estado en curso

Como Owner quiero identificar dias que quedaron `IN_PROGRESS` demasiado tiempo.

Criterios de aceptacion:
1. El estado `IN_PROGRESS` es claramente visible.
2. Puedo filtrar solo dias en curso.
3. Puedo finalizar dia con decision operativa cuando aplica.

### US-OWN-012 (P1) Eliminar rutas con confirmacion fuerte

Como Owner quiero eliminar rutas solo con confirmacion explicita para evitar errores.

Criterios de aceptacion:
1. Existe modal de confirmacion antes de borrar.
2. El sistema muestra nombre de ruta afectada.
3. Tras borrar, el listado se refresca correctamente.

### US-OWN-013 (P1) Controlar navegacion externa a Google

Como Owner quiero abrir navegacion de un `RouteDay` para validar secuencia propuesta.

Criterios de aceptacion:
1. Puedo abrir enlace Google desde detalle de dia.
2. Si falla enlace, recibo mensaje claro.
3. El error no rompe la pantalla operativa.

### US-OWN-015 (P2) Revisar capacidad diaria en contexto operativo

Como Owner quiero ver capacidad, carga prevista y carga ya registrada para decidir si la planificacion diaria es razonable.

Criterios de aceptacion:
1. La jornada muestra `capacity_liters`.
2. Se informa del contexto operativo de la jornada sin exponer tecnicismos internos innecesarios.
3. La informacion visible distingue entre planificacion y ejecucion en curso.

### US-OWN-014 (P2) Vista ejecutiva de estados de semana

Como Owner quiero una lectura ejecutiva por estado para reportar operacion.

Criterios de aceptacion:
1. Existen contadores por estado de `RouteDay`.
2. Los contadores cambian al cambiar de semana.
3. Los filtros de estado aplican sobre ese conjunto.

### US-OWN-015 (P2) Tener control rapido de expansion de dias

Como Owner quiero expandir u ocultar todos los dias para navegar rapido entre semanas largas.

Criterios de aceptacion:
1. Existe accion de expandir/ocultar todos.
2. Actua sobre los dias visibles por filtro.
3. Mantiene estado de expansion coherente tras refresco.

## 8. Historias Worker (ampliacion)

### US-WRK-005 (P0) Iniciar ruta diaria con una accion

Como Worker quiero iniciar mi ruta diaria rapidamente al empezar jornada.

Criterios de aceptacion:
1. Boton iniciar disponible en estados permitidos.
2. Al iniciar, estado cambia a `IN_PROGRESS`.
3. La UI refleja el cambio sin recargar manualmente.

### US-WRK-006 (P0) Finalizar con pendientes mediante decision guiada

Como Worker quiero finalizar un dia con pendientes solo tras una decision consciente.

Criterios de aceptacion:
1. Si hay pendientes, aparece modal de decision.
2. Puedo elegir `PARTIAL` o `CANCELED`.
3. El estado final coincide con la decision tomada.

### US-WRK-007 (P1) Operar parada desde selector rapido

Como Worker quiero usar un selector de pendientes para no buscar manualmente en toda la tabla.

Criterios de aceptacion:
1. El selector muestra solo paradas operables.
2. Puedo abrir la parada seleccionada con un clic.
3. Si la parada ya no existe, recibo aviso y no se rompe flujo.

### US-WRK-008 (P1) Registrar parada con contexto minimo

Como Worker quiero ver datos clave de la parada antes de registrar.

Criterios de aceptacion:
1. Veo cliente, direccion y limite de respuesta.
2. Veo plan base de envases/litros.
3. Puedo registrar sin cambiar de pantalla.

### US-WRK-009 (P1) Forzar registro cuando hay salto de orden justificado

Como Worker quiero forzar un registro en casos excepcionales de operativa real.

Criterios de aceptacion:
1. Existe opcion `force` en modal de registro.
2. Se informa el impacto de usar forzado.
3. El backend valida y responde con trazabilidad.

### US-WRK-010 (P1) Marcar parada cancelada en campo

Como Worker quiero poder marcar parada cancelada cuando no se puede recoger.

Criterios de aceptacion:
1. Existe checkbox de marcar cancelada.
2. La parada queda en estado coherente.
3. El cierre del dia considera esas cancelaciones.

### US-WRK-011 (P2) Mantener ritmo en red movil lenta

Como Worker quiero que la UI sea tolerante a latencia para no perder tiempo.

Criterios de aceptacion:
1. Botones muestran estado cargando durante envio.
2. Se evita doble envio accidental.
3. Tras exito, se refresca solo lo necesario.

### US-WRK-012 (P2) Operar paradas en tarjetas desde movil

Como Worker quiero ver paradas en tarjetas compactas para tocar acciones facilmente.

Criterios de aceptacion:
1. En movil no dependo de tabla horizontal.
2. Cada tarjeta muestra estado y accion primaria.
3. La accion de registrar funciona igual que en desktop.

## 9. Historias Client (ampliacion)

### US-CLI-004 (P1) Ver claramente solicitudes expiradas

Como Client quiero identificar cuando una solicitud ya expiro para entender por que no puedo responder.

Criterios de aceptacion:
1. Se muestra estado/limite de cada solicitud.
2. Si expiro, la accion responder no esta disponible.
3. El mensaje de bloqueo es claro.

### US-CLI-005 (P1) Entender origen del valor final

Como Client quiero saber si el valor final fue respondido por mi, autoestimado o manual.

Criterios de aceptacion:
1. Se muestra estado final de solicitud.
2. Se distingue `ANSWERED`, `AUTO_ESTIMATED`, `MANUAL`.
3. La vista evita ambiguedades para el usuario.

### US-CLI-006 (P1) Consultar historico sin ruido de otras empresas

Como Client quiero garantia de aislamiento de datos para confiar en la plataforma.

Criterios de aceptacion:
1. Solo veo mis solicitudes y recogidas.
2. No puedo acceder por URL a recursos ajenos.
3. El backend responde `403/404` en accesos no autorizados.

### US-CLI-007 (P2) Navegar desde movil por solicitudes

Como Client quiero consultar y responder solicitudes desde movil sin friccion.

Criterios de aceptacion:
1. Listados y formularios se adaptan a pantalla pequena.
2. Botones y campos son tocables y legibles.
3. El flujo completo se puede completar desde movil.

### US-CLI-008 (P2) Ver perfil personal con datos coherentes

Como Client quiero ver un perfil limpio y consistente para gestionar mis datos.

Criterios de aceptacion:
1. Solo se muestran atributos relevantes al rol.
2. Puedo actualizar datos permitidos.
3. Puedo cambiar contrasena desde seccion de seguridad.

### US-CLI-009 (P2) Revisar trazabilidad temporal de solicitudes

Como Client quiero ver fechas clave para entender ciclo de mi solicitud.

Criterios de aceptacion:
1. Se muestra fecha limite y estado actual.
2. Se puede inferir si hubo autoestimacion.
3. Las fechas se muestran en formato local legible.

### US-CLI-010 (P2) Reducir errores al responder litros

Como Client quiero validaciones claras para no enviar datos incorrectos.

Criterios de aceptacion:
1. El formulario valida dato numerico positivo.
2. Si hay error, se muestra mensaje especifico.
3. Tras envio correcto, la lista refleja nuevo estado.

## 10. Historias de maestros y catalogos

### US-MST-001 (P0) Gestionar clientes de forma completa

Como Owner quiero mantener clientes (alta, edicion, baja logica) para sostener operativa.

Criterios de aceptacion:
1. CRUD disponible con validaciones de negocio.
2. Filtros y busqueda por campos clave.
3. Integracion con rutas y recogidas activa.

### US-MST-002 (P0) Gestionar trabajadores de empresa

Como Owner quiero gestionar trabajadores y su estado para cubrir rutas.

Criterios de aceptacion:
1. CRUD y activacion/desactivacion disponibles.
2. Restriccion por empresa aplicada.
3. Datos reflejados en rutas asignadas.

### US-MST-003 (P0) Gestionar camiones y conductor

Como Owner quiero asignar conductor a camion para planificar ejecucion.

Criterios de aceptacion:
1. CRUD de camiones funcional.
2. Asignacion de conductor valida rol/empresa.
3. Errores de conflicto se informan claramente.

### US-MST-004 (P1) Gestionar zonas geograficas sin solape no deseado

Como Owner quiero definir zonas claras para evitar ambiguedad en asignacion de clientes.

Criterios de aceptacion:
1. Puedo crear y editar poligonos.
2. El sistema avisa de incoherencias basicas.
3. Las zonas se usan en generacion semanal.

### US-MST-005 (P1) Buscar rapidamente entidades

Como usuario de gestion quiero busqueda transversal por listados para ganar velocidad.

Criterios de aceptacion:
1. Los listados soportan `search`.
2. La busqueda combina varios atributos relevantes.
3. El rendimiento es aceptable en dataset medio.

### US-MST-006 (P2) Ver indicadores en detalles de cliente y worker

Como Owner quiero ver estadisticas resumidas para tomar decisiones.

Criterios de aceptacion:
1. Se muestran KPIs coherentes con estados reales.
2. No se contabilizan estados inexistentes.
3. Litros e importes reflejan reglas de negocio vigentes.

## 11. Historias de plataforma, seguridad y operacion

### US-PLT-006 (P0) Manejo consistente de errores API

Como sistema quiero respuestas de error consistentes para simplificar frontend y soporte.

Criterios de aceptacion:
1. Estructura de error uniforme en endpoints clave.
2. Mensajes de validacion comprensibles.
3. Errores internos quedan logueados.

### US-PLT-007 (P0) Logging estandarizado

Como equipo quiero logs uniformes para diagnosticar incidencias rapido.

Criterios de aceptacion:
1. Formato `[archivo - funcion] mensaje` en logs funcionales.
2. Nivel de severidad correcto (`info/warning/error`).
3. Eventos criticos de rutas quedan trazados.

### US-PLT-008 (P1) Locks de concurrencia en generacion semanal

Como sistema quiero blindar generacion frente a ejecuciones simultaneas.

Criterios de aceptacion:
1. Existe lock por ruta y semana.
2. Segunda peticion conflictiva no duplica plan.
3. El lock se libera correctamente tras error o exito.

### US-PLT-009 (P1) Idempotencia en acciones de schedule

Como sistema quiero reprogramar tareas sin acumulacion de duplicados.

Criterios de aceptacion:
1. CollectionRequest mantiene referencia de task activa.
2. Reprogramacion revoca task previa cuando aplica.
3. No quedan tareas huerfanas por regeneraciones repetidas.

### US-PLT-010 (P1) Permisos dedicados para acciones sensibles

Como sistema quiero permisos especificos para acciones operativas de riesgo.

Criterios de aceptacion:
1. Generar semana exige permiso de empresa/rol.
2. Manual de solicitudes exige rol autorizado.
3. En denegacion se devuelve estado HTTP correcto.

### US-PLT-011 (P1) Fallback robusto de servicios externos

Como sistema quiero continuidad operativa aunque fallen Google o email.

Criterios de aceptacion:
1. Si Google falla, se conserva orden base sin romper flujo.
2. Si email falla, no bloquea generacion de semana.
3. El fallo queda registrado para soporte.

### US-PLT-012 (P1) Control de calidad de fixtures

Como equipo quiero fixtures realistas para validar escenarios operativos.

Criterios de aceptacion:
1. Existen datos de recogida recientes y variados.
2. Predominan casos reales de bidones.
3. Hay cobertura de frecuencias y estados diversos.

### US-PLT-012B (P1) Fixtures economicas utiles

Como equipo quiero fixtures de compradores, ventas y datos fiscales para probar el modulo economico desde el primer arranque.

Criterios de aceptacion:
1. Existen compradores demo listos para seleccionar en ventas.
2. Existen ventas demo con numero de factura manual y fechas coherentes.
3. La configuracion global incluye datos fiscales basicos para regenerar PDFs sin edicion previa.

### US-PLT-013 (P2) Observabilidad de tareas Celery

Como equipo quiero visibilidad de tareas para actuar ante retrasos o fallos.

Criterios de aceptacion:
1. Tareas criticas tienen nombre y log identificables.
2. Retries quedan trazados con contexto util.
3. Se puede auditar resultado por solicitud/ruta.

### US-PLT-014 (P2) Versionado de decisiones funcionales

Como equipo quiero registrar cambios de reglas para evitar regresiones.

Criterios de aceptacion:
1. Cambios relevantes quedan en docs fechados.
2. Existe historial de revisiones documentales del proyecto.
3. El equipo puede reconstruir por que se cambio una regla.

### US-PLT-015 (P2) Calidad de respuestas para frontend

Como frontend quiero payloads coherentes para minimizar parches locales.

Criterios de aceptacion:
1. Estados y etiquetas devueltos son consistentes.
2. Campos clave no cambian forma inesperadamente.
3. Las pantallas no dependen de hardcodes fragiles.

### US-PLT-015B (P1) Parametros globales extensibles por empresa

Como sistema quiero centralizar parametros globales de empresa para evitar hardcodes dispersos y facilitar evolucion futura.

Criterios de aceptacion:
1. Existe un modelo dedicado de configuracion global por empresa.
2. El precio por litro se resuelve desde esa configuracion cuando no se informa manualmente.
3. La estructura permite ampliar despues con IVA, IRPF u otras reglas.

### US-PLT-016 (P2) Limites de seguridad de API key externa

Como Owner tecnico quiero proteger costes y abuso de APIs externas.

Criterios de aceptacion:
1. API keys se gestionan por entorno.
2. Existen restricciones de uso en proveedor.
3. Hay trazabilidad de consumo para control de coste.

### US-PLT-017 (P2) Integridad de estados operativos

Como sistema quiero evitar transiciones invalidas para preservar datos.

Criterios de aceptacion:
1. `RouteDay` respeta maquina de estados definida.
2. `CollectionRequest` respeta estados permitidos por accion.
3. `Collection` mantiene coherencia con registro de parada.

### US-PLT-018 (P2) Resiliencia de UX ante recargas

Como usuario quiero conservar contexto operativo al refrescar pantalla.

Criterios de aceptacion:
1. Filtros de semana/estado se pueden reaplicar rapido.
2. No se pierde la capacidad de continuar operacion tras refresh.
3. La pantalla vuelve a estado valido tras errores temporales.

### US-PLT-019 (P2) Acceso seguro en admin

Como equipo quiero que el admin no rompa por campos obsoletos.

Criterios de aceptacion:
1. Config de admin usa campos reales del modelo.
2. Pantallas de admin cargan sin `FieldError`.
3. Cambios de modelo actualizan admin asociado.

### US-PLT-020 (P2) Preparacion para pruebas E2E

Como equipo quiero historias trazables para convertirlas en pruebas.

Criterios de aceptacion:
1. Cada flujo P0 tiene criterio verificable.
2. Existen datos semilla suficientes para ejecutar casos.
3. Se puede mapear historia -> test sin ambiguedad.

## 12. Historias de integracion y notificaciones

### US-INT-001 (P1) Notificar creacion de solicitud

Como sistema quiero notificar al cliente cuando se crea su solicitud.

Criterios de aceptacion:
1. Al crear solicitud se encola tarea de notificacion.
2. El fallo de envio no bloquea operacion.
3. El intento queda registrado en logs.

### US-INT-002 (P1) Autoestimar al vencer limite

Como sistema quiero ejecutar autoestimacion al expirar plazo.

Criterios de aceptacion:
1. Task se ejecuta en `expires_at` o inmediata si ya paso.
2. Solicitud cambia a estado `AUTO_ESTIMATED` cuando corresponda.
3. Se preserva trazabilidad de origen del valor.

### US-INT-003 (P2) Integrar navegacion Google desde ruta diaria

Como usuario operativo quiero exportar ruta diaria a Google Maps.

Criterios de aceptacion:
1. Se genera URL valida con origen/waypoints.
2. La URL respeta orden operativo del dia.
3. Se abre en nueva pestana sin romper app.

### US-INT-004 (P2) Reemplazar canales de email sin tocar negocio

Como equipo quiero desacoplar proveedor de email del flujo funcional.

Criterios de aceptacion:
1. Logica de negocio no depende de libreria concreta de envio.
2. El adaptador de envio es intercambiable por entorno.
3. La falla del proveedor no interrumpe tareas operativas.

### US-INT-005 (P2) Deteccion de credenciales invalidas

Como equipo quiero detectar rapido errores de credenciales en integraciones.

Criterios de aceptacion:
1. Mensajes de error son claros en logs.
2. Se distingue error transitorio de credencial invalida.
3. Existe plan de reintentos razonable.

## 13. Historias de datos, reporting y auditoria

### US-DAT-001 (P1) Coherencia de calculo de litros en estadisticas

Como Owner quiero que KPI de litros use reglas de negocio correctas.

Criterios de aceptacion:
1. Se excluyen recogidas canceladas donde corresponda.
2. Los agregados coinciden con detalle de registros.
3. Metrica mantiene consistencia entre pantallas.

### US-DAT-002 (P1) Coherencia de ingresos en estadisticas

Como Owner quiero ver ingresos basados en recogidas validas.

Criterios de aceptacion:
1. Solo estados validos impactan ingresos.
2. Los importes se agregan sin duplicados.
3. El dato mensual es consistente con historico.

### US-DAT-002B (P1) Consistencia del precio por defecto en recogidas

Como Owner quiero que el precio usado por defecto en recogidas sea estable y auditable.

Criterios de aceptacion:
1. Existe un valor global visible para la empresa.
2. Las recogidas nuevas lo usan salvo override manual.
3. El detalle de recogida sigue mostrando el valor finalmente guardado.

### US-DAT-002C (P1) Consistencia economica entre compras y ventas

Como Owner quiero que el panel economico combine correctamente costes de recogidas e ingresos de ventas.

Criterios de aceptacion:
1. El resumen economico separa `total_cost` y `total_income`.
2. El beneficio neto se calcula como `income - cost`.
3. El volumen comprado y el volumen vendido se muestran por separado.

### US-DAT-002D (P1) Controlar si una recogida computa economicamente

Como Owner quiero decidir si una recogida es facturable para excluir casos internos o excepcionales del reporting economico.

Criterios de aceptacion:
1. Una recogida puede marcarse como `Facturable` o `No facturable` en alta y edicion.
2. El detalle y el listado muestran claramente ese estado.
3. Solo las recogidas confirmadas y facturables computan como coste en estadisticas.

### US-DAT-003 (P2) Auditoria de acciones manuales

Como Owner quiero saber quien hizo ajustes manuales sensibles.

Criterios de aceptacion:
1. Acciones manuales guardan usuario y fecha.
2. Se pueden consultar en detalle de entidad.
3. Los logs complementan la auditoria persistida.

### US-DAT-004 (P2) Exportacion operativa basica

Como Owner quiero exportar datos clave para control externo.

Criterios de aceptacion:
1. Se puede exportar resumen de rutas/recogidas.
2. El formato es legible por herramientas comunes.
3. La exportacion respeta permisos por empresa.

### US-DAT-005 (P2) Trazabilidad de estados en RouteDay

Como equipo quiero seguir la evolucion de estado de cada dia operativo.

Criterios de aceptacion:
1. Los cambios de estado quedan reflejados en eventos o logs.
2. Se puede explicar por que un dia quedo parcial/cancelado.
3. Los datos permiten soporte post-incidencia.

## 14. Historias UX movil avanzadas

### US-UXM-003 (P1) Botones operativos grandes en zona pulgar

Como usuario movil quiero botones principales accesibles con el pulgar.

Criterios de aceptacion:
1. Acciones clave tienen tamano tactil adecuado.
2. No se solapan controles en resoluciones pequenas.
3. La jerarquia visual destaca accion primaria.

### US-UXM-004 (P1) Contenido sin zoom manual

Como usuario movil quiero leer informacion sin hacer zoom.

Criterios de aceptacion:
1. Tipografia y espaciado son legibles en 360px.
2. Tablas complejas tienen alternativa adaptada.
3. Etiquetas y estados no quedan cortados criticamente.

### US-UXM-005 (P1) Flujos de modal ergonomicos en movil

Como usuario movil quiero completar modales sin esfuerzo.

Criterios de aceptacion:
1. Modales no exceden alto util de pantalla.
2. Campos y botones quedan visibles con teclado abierto.
3. El cierre accidental se minimiza.

### US-UXM-006 (P2) Feedback inmediato tras accion

Como usuario movil quiero confirmacion rapida tras cada accion.

Criterios de aceptacion:
1. Se muestra snackbar o estado visual tras exito/error.
2. Boton refleja `loading` durante operacion.
3. No hay incertidumbre sobre si se ejecuto la accion.

### US-UXM-007 (P2) Persistencia del contexto visual

Como usuario movil quiero mantener foco en el dia/parada que estaba operando.

Criterios de aceptacion:
1. Los despliegues no se resetean sin necesidad.
2. El filtro activo se mantiene durante trabajo.
3. El refresco no obliga a rehacer navegacion larga.

### US-UXM-008 (P2) Priorizacion de informacion critica

Como usuario movil quiero ver primero lo importante para decidir rapido.

Criterios de aceptacion:
1. Estado, pendientes y accion principal aparecen arriba.
2. Datos secundarios quedan en secciones plegables o menos prominentes.
3. Se reduce carga cognitiva en campo.

### US-UXM-009 (P2) Navegacion consistente entre roles en movil

Como usuario quiero una experiencia estable al cambiar de rol.

Criterios de aceptacion:
1. Patrones de navegacion son consistentes.
2. Solo cambia contenido autorizado por rol.
3. El acceso a perfil y logout es claro.

### US-UXM-010 (P2) Modo operacion continua

Como usuario de campo quiero ejecutar varias paradas seguidas con minimo taps.

Criterios de aceptacion:
1. Selector de parada propone siguiente pendiente.
2. Tras registrar, la lista se actualiza y mantiene contexto.
3. El tiempo medio por parada se reduce respecto al flujo base.

## 15. Historias de documentacion y gobernanza

### US-DOC-001 (P1) Mantener inventario de pantallas actualizado

Como equipo quiero inventario de pantallas para detectar gaps funcionales.

Criterios de aceptacion:
1. Cada pantalla tiene ruta y archivo.
2. Se indica estado real de implementacion.
3. Se revisa en cada hito funcional.

### US-DOC-002 (P1) Mantener API funcional viva

Como equipo quiero API documentada para alinear backend y frontend.

Criterios de aceptacion:
1. Endpoints operativos aparecen en `API.md`.
2. Se documentan acciones custom y filtros.
3. Se incluyen ejemplos minimos de uso.

### US-DOC-003 (P2) Publicar revisiones documentales por fecha

Como equipo quiero snapshots de estado para trazabilidad de proyecto.

Criterios de aceptacion:
1. Cada revision documental relevante deja referencia fechada.
2. Incluye cambios, validacion y riesgos.
3. Sirve de base para siguiente iteracion.

### US-DOC-004 (P2) Definir backlog priorizado de historias

Como Product Owner quiero priorizar trabajo con claridad.

Criterios de aceptacion:
1. Historias etiquetadas por prioridad.
2. Cada historia tiene criterios verificables.
3. Backlog se puede convertir a tareas tecnicas.

### US-DOC-005 (P2) Trazar dependencia entre historias y modulos

Como equipo quiero identificar impacto de cambios rapidamente.

Criterios de aceptacion:
1. Historias se agrupan por rol y dominio.
2. Se distinguen historias funcionales y tecnicas.
3. Se facilita estimacion y planificacion por sprint.

## 16. Observaciones de mantenimiento del backlog

Este documento combina historias:

- funcionales
- tecnicas
- de calidad
- de UX movil
- de documentacion y gobierno

Por ello conviene leerlo junto con:

- `docs/REQUISITOS.md`
- `docs/CASOS_DE_USO.md`
- `docs/FUNCIONAL.md`
- `docs/TESTING.md`

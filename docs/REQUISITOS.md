# Catalogo de Requisitos GreenPath

Fecha de revision: 2026-04-30

## 1. Objetivo del documento

Este documento consolida los requisitos del sistema GreenPath con un enfoque mas formal y mas cercano al que se espera en una memoria de TFG o en una especificacion de producto madura.

Su objetivo es complementar:

- `docs/FUNCIONAL.md`, que explica el negocio y los procesos
- `docs/API.md`, que documenta contratos tecnicos
- `docs/MEMORIA_FUNCIONAL_TFG.md`, que resume el proyecto con tono academico

Aqui se recopilan requisitos de varios tipos:

- requisitos de negocio
- requisitos de informacion
- requisitos funcionales
- requisitos no funcionales
- requisitos de interfaz
- requisitos de integracion
- requisitos de seguridad y trazabilidad
- requisitos de despliegue, testing y documentacion

El catalogo debe leerse teniendo en cuenta que GreenPath es una plataforma multiempresa con una operativa real compleja: combina reglas logisticas, geografia, procesos asincronos, facturacion bajo demanda, configuracion fiscal editable y separacion estricta entre operacion en calle, cierre economico y reporting.

## 2. Criterio de clasificacion

Para facilitar la lectura, los requisitos se clasifican con los siguientes prefijos:

- `RB`: requisito de negocio
- `RI`: requisito de informacion
- `RF`: requisito funcional
- `RNF`: requisito no funcional
- `RINT`: requisito de interfaz
- `RIE`: requisito de integracion externa
- `RSEG`: requisito de seguridad y trazabilidad
- `ROPS`: requisito operativo, de despliegue o de calidad

## 3. Actores considerados

| Actor | Descripcion |
| --- | --- |
| Owner | Usuario con control completo del negocio y de la configuracion |
| Worker | Usuario operativo que ejecuta rutas y registra recogidas |
| Client | Usuario externo asociado a un cliente de recogida |
| Buyer | Entidad interna de facturacion sin acceso a la plataforma |
| Sistema | Procesos automaticos y asincronos del propio producto |

## 4. Requisitos de negocio

| Codigo | Requisito |
| --- | --- |
| RB-001 | El sistema debe permitir planificar la recogida de aceite usado por semanas operativas. |
| RB-002 | El sistema debe diferenciar entre planificacion y ejecucion real de la ruta. |
| RB-003 | El sistema debe permitir consultar que clientes corresponden a cada jornada operativa. |
| RB-004 | El sistema debe poder solicitar al cliente una estimacion previa de litros. |
| RB-005 | El sistema debe poder continuar operando aunque el cliente no responda a tiempo. |
| RB-006 | El sistema debe registrar la recogida real realizada en cada parada. |
| RB-007 | El sistema debe permitir una medicion posterior en nave antes del cierre economico de la recogida. |
| RB-008 | El sistema debe distinguir entre recogidas facturables y no facturables. |
| RB-009 | El sistema debe contemplar tanto dinero invertido en recogidas como dinero ingresado en ventas. |
| RB-010 | El sistema debe permitir registrar compradores internos para la facturacion de ventas. |
| RB-011 | El sistema debe generar facturas PDF de venta. |
| RB-012 | El sistema debe mantener configurables los datos fiscales y operativos de la empresa. |
| RB-013 | El sistema debe ofrecer estadisticas operativas y economicas. |
| RB-014 | Todo el bloque de gestion economica y configuracion avanzada debe quedar restringido al owner. |
| RB-015 | La plataforma debe poder operar por empresa, aislando datos y permisos. |

## 5. Requisitos de informacion

| Codigo | Informacion necesaria | Finalidad |
| --- | --- | --- |
| RI-001 | Datos de empresa | Identidad y pertenencia del sistema |
| RI-002 | Datos fiscales de empresa | Facturacion PDF y configuracion economica |
| RI-003 | Hub de empresa | Punto de salida operativo |
| RI-004 | Datos de cliente | Operacion de recogida e historico |
| RI-005 | Ubicacion del cliente | Filtros GIS, mapas y rutas |
| RI-006 | Frecuencia de cliente | Planificacion semanal coherente |
| RI-007 | Datos de trabajador | Operacion diaria y permisos |
| RI-008 | Datos de camion | Asignacion de flota |
| RI-009 | Poligonos de zona | Cobertura geografica de rutas |
| RI-010 | Ruta plantilla | Definicion recurrente de operacion |
| RI-011 | Relacion zona-dia | Configuracion de cobertura por dia de ruta |
| RI-012 | Jornada operativa | Ejecucion real de una fecha concreta |
| RI-013 | Parada operativa | Cliente concreto dentro de una jornada |
| RI-014 | Solicitud de estimacion | Dato previo a la recogida |
| RI-015 | Recogida real | Resultado operativo y economico |
| RI-016 | Comprador interno | Destinatario comercial y fiscal |
| RI-017 | Venta | Ingreso economico del negocio |
| RI-018 | Factura PDF | Soporte documental de la venta |
| RI-019 | Datos estadisticos | Cuadros de mando e indicadores |

## 6. Requisitos funcionales

### 6.1 Autenticacion y usuarios

| Codigo | Requisito |
| --- | --- |
| RF-001 | El sistema debe permitir login con usuario y password. |
| RF-002 | El sistema debe soportar login social cuando este configurado. |
| RF-003 | El sistema debe identificar el rol del usuario autenticado. |
| RF-004 | El sistema debe limitar el acceso a vistas, acciones y datos segun rol. |
| RF-005 | El sistema debe permitir al usuario consultar y editar su perfil. |
| RF-006 | El sistema debe permitir cambio de contrasena. |

### 6.2 Clientes

| Codigo | Requisito |
| --- | --- |
| RF-007 | El owner debe poder crear, editar, listar y consultar clientes. |
| RF-008 | El sistema debe almacenar direccion y datos de contacto del cliente. |
| RF-009 | El sistema debe intentar geocodificar automaticamente al cliente desde su direccion. |
| RF-010 | El sistema debe permitir definir frecuencia de recogida del cliente. |
| RF-011 | El client debe poder consultar sus solicitudes de recogida. |
| RF-012 | El client debe poder consultar su historico de recogidas. |

### 6.3 Trabajadores y camiones

| Codigo | Requisito |
| --- | --- |
| RF-013 | El owner debe poder crear, editar, listar y consultar trabajadores. |
| RF-014 | El front de negocio solo debe crear trabajadores normales, no owners. |
| RF-015 | El sistema debe permitir asignar un camion a un trabajador. |
| RF-016 | El owner debe poder crear, editar, listar y consultar camiones. |
| RF-017 | El sistema debe mostrar el camion asignado en el detalle del trabajador cuando exista. |

### 6.4 Zonas y rutas plantilla

| Codigo | Requisito |
| --- | --- |
| RF-018 | El owner debe poder crear, editar, listar y consultar zonas geograficas. |
| RF-019 | El owner debe poder crear, editar, listar y consultar rutas plantilla. |
| RF-020 | Una ruta debe permitir asociar zonas por dia de semana. |
| RF-021 | Una ruta debe poder asociarse a un trabajador responsable. |
| RF-022 | La interfaz de detalle de ruta debe permitir consultar de forma clara la configuracion semanal. |

### 6.5 Generacion semanal

| Codigo | Requisito |
| --- | --- |
| RF-023 | El owner debe poder generar una semana operativa a partir de una ruta plantilla. |
| RF-024 | La generacion debe aceptar capacidad global o capacidad especifica por fecha. |
| RF-025 | La generacion debe ser idempotente. |
| RF-026 | La opcion `regenerate` debe permitir rehacer la semana solo cuando siga siendo editable. |
| RF-027 | El sistema debe crear o actualizar `RouteDay` y `RouteDayClient`. |
| RF-028 | El sistema debe filtrar clientes por pertenencia geografica a las zonas del dia. |
| RF-029 | El sistema debe respetar la frecuencia del cliente y la planificacion previa dentro de la misma empresa. |
| RF-030 | El sistema debe aplicar limites operativos de capacidad y maximo de clientes por jornada. |
| RF-031 | El sistema debe poder optimizar el orden inicial de paradas con Google Directions cuando proceda. |
| RF-032 | El sistema debe crear las solicitudes de estimacion asociadas a las paradas generadas. |

### 6.6 Solicitudes al cliente

| Codigo | Requisito |
| --- | --- |
| RF-033 | El sistema debe crear `CollectionRequest` para las paradas planificadas. |
| RF-034 | Cada solicitud debe tener una fecha de expiracion calculada automaticamente. |
| RF-035 | El client debe poder responder tipo y cantidad de envases desde su portal. |
| RF-036 | Owner o worker deben poder resolver manualmente una solicitud cuando aplique. |
| RF-037 | Si una solicitud expira, el sistema debe poder autoestimar litros de forma asincrona. |
| RF-038 | El sistema debe registrar quien resolvio la solicitud y como se resolvio. |

### 6.7 Ejecucion diaria de ruta

| Codigo | Requisito |
| --- | --- |
| RF-039 | Owner y worker autorizados deben poder abrir la vista de ejecucion de ruta. |
| RF-040 | El sistema debe permitir iniciar una jornada. |
| RF-041 | El sistema debe permitir seleccionar la siguiente parada activa. |
| RF-042 | El sistema debe permitir registrar una parada como recogida o cancelada. |
| RF-043 | El sistema debe permitir finalizar una jornada con el estado que corresponda. |
| RF-044 | El sistema debe poder abrir la navegacion de Google Maps desde la interfaz operativa. |
| RF-045 | La vista de ejecucion debe mostrar mapa, orden de paradas y estado operativo. |
| RF-045A | La vista de ejecucion debe sugerir la siguiente parada operativa correcta y presentar una interfaz simplificada para campo. |
| RF-045B | Cuando la capacidad diaria obligue a dividir la jornada, el sistema debe poder reflejar el retorno implicito al hub tanto en la operacion visual como en la navegacion externa. |

### 6.8 Recogidas

| Codigo | Requisito |
| --- | --- |
| RF-046 | El owner debe poder crear, editar, listar y consultar recogidas. |
| RF-047 | Una recogida debe poder nacer desde operacion de ruta o desde alta manual. |
| RF-048 | Una recogida debe admitir estado pendiente de medicion, confirmada o cancelada. |
| RF-049 | El sistema debe permitir introducir litros medidos, deducciones y precio por litro. |
| RF-050 | El sistema debe permitir marcar una recogida como facturable o no facturable. |
| RF-051 | El detalle de recogida debe mostrar claramente si es facturable. |
| RF-052 | El listado de recogidas debe permitir filtrar por `billable`. |

### 6.9 Compradores, ventas y facturacion

| Codigo | Requisito |
| --- | --- |
| RF-053 | El owner debe poder crear, editar, listar y consultar compradores internos. |
| RF-054 | Los compradores no deben tener acceso a la plataforma. |
| RF-055 | El owner debe poder crear, editar, listar y consultar ventas. |
| RF-056 | Una venta debe seleccionar un comprador. |
| RF-057 | Una venta debe almacenar numero de factura, fecha de factura, concepto, cantidad, unidad y precio unitario. |
| RF-058 | El sistema debe recalcular subtotal, impuesto y total de la venta. |
| RF-059 | El sistema debe generar un PDF de factura para cada venta. |
| RF-060 | El sistema debe permitir descargar la factura PDF generandola bajo demanda con los datos vigentes. |
| RF-060A | El formulario de venta debe mostrar como ayuda el numero de la ultima factura registrada sin autocompletar el campo. |
| RF-060B | El formulario de venta debe usar `kg` como unidad por defecto. |
| RF-060C | El formulario de alta y edicion de venta debe permitir reusar conceptos anteriores sin modificar la unidad seleccionada. |

### 6.10 Configuracion y estadisticas

| Codigo | Requisito |
| --- | --- |
| RF-061 | El owner debe poder editar la configuracion global de empresa. |
| RF-062 | La configuracion debe permitir mantener precio por litro, hub y datos fiscales. |
| RF-063 | El hub de empresa debe poder fijarse sobre un mapa. |
| RF-064 | La pantalla de estadisticas debe mostrar costes, ingresos y beneficio neto. |
| RF-065 | Las estadisticas deben diferenciar claramente entre operacion y economia. |
| RF-066 | Solo las recogidas confirmadas y facturables deben computar como coste. |
| RF-067 | Las ventas deben computar como ingreso. |

### 6.11 Dashboard, filtros y consulta ejecutiva

| Codigo | Requisito |
| --- | --- |
| RF-068 | El sistema debe ofrecer un dashboard ejecutivo para owner y redireccionar a worker/client a sus pantallas operativas iniciales. |
| RF-069 | El owner debe poder consultar actividad reciente del sistema. |
| RF-070 | El dashboard debe ofrecer accesos rapidos a las acciones mas frecuentes. |
| RF-071 | Los listados deben permitir busqueda por varios atributos relevantes. |
| RF-072 | Los listados deben permitir filtrado por estado cuando el modulo lo requiera. |
| RF-073 | Los listados deben soportar paginacion configurable. |
| RF-074 | Los listados deben mostrar un estado vacio cuando no existan resultados. |
| RF-075 | El sistema debe permitir ordenar o consultar datos historicos por fecha cuando aplique. |

### 6.12 Perfil, configuracion personal y sesion

| Codigo | Requisito |
| --- | --- |
| RF-076 | El usuario debe poder consultar sus datos personales desde la interfaz. |
| RF-077 | El usuario debe poder editar su informacion personal permitida. |
| RF-078 | El sistema debe permitir actualizar la imagen de perfil cuando el flujo lo contemple. |
| RF-079 | El sistema debe permitir cerrar sesion desde la interfaz principal. |
| RF-080 | La navegacion de perfil debe ser consistente con el resto de la aplicacion. |

### 6.13 Backoffice y administracion interna

| Codigo | Requisito |
| --- | --- |
| RF-081 | El sistema debe permitir administrar entidades desde Django Admin. |
| RF-082 | Los modelos principales deben contar con un admin usable para consulta y mantenimiento. |
| RF-083 | El admin debe permitir localizar rapidamente registros mediante filtros y busqueda. |
| RF-084 | El admin debe reflejar los campos realmente existentes en los modelos. |
| RF-085 | Las entidades administrativas sensibles deben mostrar informacion de contexto suficiente para su revision. |

### 6.14 Facturacion y documentos

| Codigo | Requisito |
| --- | --- |
| RF-086 | El PDF de factura debe incluir los datos fiscales de emisor y comprador. |
| RF-087 | El PDF de factura debe incluir numero de factura, fecha, concepto, base, IVA y total. |
| RF-088 | El sistema debe permitir volver a descargar la factura generandola de nuevo con los datos vigentes sin recrear manualmente la venta. |
| RF-089 | El nombre del fichero PDF debe ser consistente con el numero de factura. |
| RF-090 | El sistema debe permitir adaptar el contenido documental mediante configuracion editable de empresa. |

### 6.15 Calidad del dato y reglas de consistencia

| Codigo | Requisito |
| --- | --- |
| RF-091 | El sistema debe evitar que un cliente se planifique en jornadas incompatibles con su frecuencia. |
| RF-092 | El sistema debe evitar que una jornada operada se regenere sin cumplir las condiciones de negocio. |
| RF-093 | El sistema debe mantener coherencia entre venta, factura y PDF asociado. |
| RF-094 | El sistema debe sincronizar la fecha interna de venta con la fecha de factura visible. |
| RF-095 | El sistema debe mantener coherencia entre estado de jornada y estado de sus paradas procesadas. |
| RF-096 | El sistema debe impedir, en la medida de lo posible, operaciones que degraden la trazabilidad del historico. |

### 6.16 Notificaciones y comunicacion

| Codigo | Requisito |
| --- | --- |
| RF-097 | El sistema debe poder enviar notificaciones de acceso a nuevos usuarios cuando la integracion de correo este disponible. |
| RF-098 | El sistema debe poder enviar notificaciones de solicitud de recogida al cliente. |
| RF-099 | Los correos del sistema deben mantener una linea visual coherente entre si. |
| RF-100 | El sistema debe poder omitir el envio de un correo sin bloquear el flujo principal si la integracion no esta disponible. |
| RF-101 | Las tareas de notificacion diferida deben dejar trazabilidad suficiente para soporte. |
| RF-102 | El contenido de las notificaciones debe ser comprensible para usuarios no tecnicos. |

### 6.17 Exportacion, descarga y soporte documental

| Codigo | Requisito |
| --- | --- |
| RF-103 | El sistema debe permitir descargar documentos PDF asociados a ventas. |
| RF-104 | El sistema debe reconstruir el documento PDF con los datos vigentes cada vez que se descargue. |
| RF-105 | Los documentos generados deben mantener un formato reutilizable y legible. |
| RF-106 | El sistema debe poder mostrar o enlazar informacion documental desde el detalle de la entidad correspondiente. |
| RF-107 | El nombre de descarga del documento debe seguir una nomenclatura consistente. |
| RF-108 | La documentacion generada debe usar datos configurables de empresa y no valores fijos. |

### 6.18 Operacion economica avanzada

| Codigo | Requisito |
| --- | --- |
| RF-109 | El sistema debe permitir identificar que recogidas participan en el coste economico agregado. |
| RF-110 | El sistema debe diferenciar claramente entre historico operativo e historico economico. |
| RF-111 | El sistema debe permitir consultar ventas por periodo y por comprador. |
| RF-112 | El sistema debe poder recalcular importes derivados de una venta al editarla. |
| RF-113 | El sistema debe impedir inconsistencias basicas entre base imponible, impuesto y total. |
| RF-114 | El owner debe poder consultar un resumen economico agregado. |
| RF-115 | El sistema debe permitir mantener datos fiscales suficientes para una factura funcionalmente valida. |

### 6.19 Configuracion de empresa y parametrizacion

| Codigo | Requisito |
| --- | --- |
| RF-116 | El sistema debe permitir restablecer valores de configuracion desde la interfaz cuando proceda. |
| RF-117 | El sistema debe permitir guardar de forma independiente los distintos bloques de configuracion. |
| RF-118 | El sistema debe permitir limpiar o quitar el hub de empresa. |
| RF-119 | El sistema debe permitir parametrizar datos fiscales sin modificar codigo. |
| RF-120 | El sistema debe permitir parametrizar datos operativos globales sin modificar codigo. |
| RF-121 | Los cambios en configuracion deben impactar en los flujos que dependen de ellos a partir de ese momento. |

### 6.20 Administracion y mantenimiento funcional

| Codigo | Requisito |
| --- | --- |
| RF-122 | El sistema debe permitir al owner mantener los principales datos maestros desde la aplicacion. |
| RF-123 | El sistema debe permitir a administracion interna completar operaciones avanzadas desde Django Admin. |
| RF-124 | El sistema debe permitir revisar registros historicos sin necesidad de alterar su estado. |
| RF-125 | El sistema debe facilitar el diagnostico de incidencias funcionales mediante informacion de contexto suficiente. |
| RF-126 | La plataforma debe favorecer operaciones de demostracion o revision mediante fixtures y datos de ejemplo. |

### 6.21 Consulta historica y analitica

| Codigo | Requisito |
| --- | --- |
| RF-127 | El sistema debe permitir consultar historicos por entidad relevante. |
| RF-128 | El sistema debe ofrecer una lectura resumida del rendimiento operativo. |
| RF-129 | El sistema debe ofrecer una lectura resumida del rendimiento economico. |
| RF-130 | El sistema debe permitir distinguir estados validos de recogidas, solicitudes y jornadas en las vistas historicas. |
| RF-131 | El sistema debe permitir usar filtros de busqueda amplios en los modulos con volumen de datos. |
| RF-132 | El sistema debe poder reflejar claramente cuando un conjunto de datos no tiene resultados. |

## 7. Requisitos no funcionales

### 7.1 Arquitectura y mantenibilidad

| Codigo | Requisito |
| --- | --- |
| RNF-001 | El sistema debe estar organizado por dominios funcionales. |
| RNF-002 | La logica de negocio critica debe concentrarse en backend. |
| RNF-003 | La documentacion debe mantenerse separada por tipo de documento. |
| RNF-004 | El codigo debe poder evolucionar sin mezclar modulos no relacionados. |
| RNF-005 | El sistema debe evitar hardcodes funcionales en configuracion de empresa. |

### 7.2 Rendimiento y eficiencia

| Codigo | Requisito |
| --- | --- |
| RNF-006 | La generacion semanal debe ejecutarse en tiempos razonables para un volumen operativo medio. |
| RNF-007 | El uso de integraciones externas no debe bloquear innecesariamente la API. |
| RNF-008 | Las tareas diferidas deben trasladarse a Celery cuando no formen parte estricta de la respuesta inmediata. |
| RNF-009 | Los listados deben soportar paginacion y filtros. |

### 7.3 Seguridad y privacidad

| Codigo | Requisito |
| --- | --- |
| RNF-010 | El sistema debe autenticar usuarios antes de exponer datos privados. |
| RNF-011 | El acceso a datos debe restringirse por empresa. |
| RNF-012 | Las operaciones owner-only deben quedar protegidas por permisos dedicados. |
| RNF-013 | Las credenciales de servicios externos deben mantenerse fuera de codigo. |
| RNF-014 | El sistema no debe exponer datos sensibles innecesarios en respuestas API. |

### 7.4 Usabilidad y experiencia de usuario

| Codigo | Requisito |
| --- | --- |
| RNF-015 | La aplicacion debe ser usable en escritorio y en movil. |
| RNF-016 | Las pantallas operativas de rutas deben priorizar la claridad y el uso tactil. |
| RNF-017 | Los formularios deben ofrecer feedback coherente de errores. |
| RNF-018 | Los listados deben mantener patrones visuales consistentes. |
| RNF-019 | La navegacion debe adaptarse al rol del usuario. |

### 7.5 Fiabilidad y tolerancia a fallos

| Codigo | Requisito |
| --- | --- |
| RNF-020 | El sistema debe tolerar la ausencia temporal de integraciones opcionales. |
| RNF-021 | Los fallos de Google o Gmail no deben impedir el flujo principal del negocio. |
| RNF-022 | El sistema debe preservar jornadas ya operadas frente a regeneraciones indebidas. |
| RNF-023 | Los errores operativos deben dejar trazabilidad en logs. |

### 7.6 Datos, trazabilidad y observabilidad

| Codigo | Requisito |
| --- | --- |
| RNF-024 | El sistema debe registrar suficiente trazabilidad sobre acciones automaticas y manuales. |
| RNF-025 | Debe existir logging consistente para procesos criticos. |
| RNF-026 | Las solicitudes de recogida deben conservar informacion de scheduling y autoria. |
| RNF-027 | Las ventas y facturas deben quedar vinculadas documentalmente. |

### 7.7 Calidad y testing

| Codigo | Requisito |
| --- | --- |
| RNF-028 | El proyecto debe disponer de pruebas backend por modulos. |
| RNF-029 | El proyecto debe disponer de pruebas frontend en modulos clave. |
| RNF-030 | La documentacion debe describir como ejecutar la validacion automatizada. |

### 7.8 Disponibilidad y continuidad de servicio

| Codigo | Requisito |
| --- | --- |
| RNF-031 | El sistema debe poder seguir operando en su flujo principal aunque falle una integracion externa opcional. |
| RNF-032 | La aplicacion debe minimizar puntos unicos de fallo en procesos operativos criticos. |
| RNF-033 | Los procesos asincronos deben reintentarse o dejar trazabilidad suficiente cuando fallen. |
| RNF-034 | El sistema debe poder reiniciarse sin perder coherencia estructural de los datos persistidos. |

### 7.9 Compatibilidad y portabilidad

| Codigo | Requisito |
| --- | --- |
| RNF-035 | El frontend debe ser utilizable en navegadores modernos de escritorio. |
| RNF-036 | El frontend debe ser utilizable en navegadores moviles modernos. |
| RNF-037 | El proyecto debe poder ejecutarse en entorno local mediante contenedores. |
| RNF-038 | La documentacion debe permitir reconstruir el entorno con dependencia minima del host local. |

### 7.10 Escalabilidad y crecimiento

| Codigo | Requisito |
| --- | --- |
| RNF-039 | La arquitectura debe permitir anadir nuevos modulos sin rehacer el sistema completo. |
| RNF-040 | El sistema debe soportar crecimiento funcional por empresa, rutas, clientes y ventas dentro de un escenario pyme razonable. |
| RNF-041 | La separacion por apps debe facilitar el mantenimiento evolutivo. |
| RNF-042 | El uso de filtros y paginacion debe permitir que los listados crezcan sin degradar de inmediato la experiencia. |

### 7.11 Accesibilidad y legibilidad

| Codigo | Requisito |
| --- | --- |
| RNF-043 | La interfaz debe mantener contraste suficiente en estados y badges relevantes. |
| RNF-044 | Los textos de accion y validacion deben ser comprensibles para usuarios no tecnicos. |
| RNF-045 | Los formularios deben asociar labels y campos de manera consistente. |
| RNF-046 | Las acciones principales deben mantenerse visibles y alcanzables en movil. |

### 7.12 Consistencia de datos y concurrencia

| Codigo | Requisito |
| --- | --- |
| RNF-047 | El sistema debe minimizar inconsistencias causadas por regeneraciones concurrentes. |
| RNF-048 | Las restricciones de unicidad deben impedir duplicidades funcionalmente invalidas. |
| RNF-049 | Los cambios de estado criticos deben estar protegidos por validaciones de negocio. |
| RNF-050 | La generacion semanal debe evitar colisiones de orden en paradas del mismo dia. |

### 7.13 Observabilidad y soporte

| Codigo | Requisito |
| --- | --- |
| RNF-051 | Los logs deben identificar archivo y funcion origen del evento. |
| RNF-052 | Los errores operativos deben poder localizarse mediante mensajes coherentes de logging. |
| RNF-053 | Las respuestas de error deben mantener un formato uniforme en la API. |
| RNF-054 | La documentacion debe facilitar el onboarding tecnico y funcional. |

### 7.14 Calidad documental

| Codigo | Requisito |
| --- | --- |
| RNF-055 | El proyecto debe mantener documentacion funcional, tecnica y de testing diferenciada. |
| RNF-056 | La documentacion debe reflejar el estado real del producto y no una version idealizada. |
| RNF-057 | La documentacion debe centralizarse en un indice claro de consulta. |
| RNF-058 | Los documentos principales deben poder reutilizarse como base de memoria academica. |

### 7.15 Privacidad, custodia y cumplimiento basico

| Codigo | Requisito |
| --- | --- |
| RNF-059 | El sistema debe tratar credenciales y secretos fuera del codigo fuente. |
| RNF-060 | Los datos personales de clientes y trabajadores deben mostrarse solo a usuarios autorizados. |
| RNF-061 | Las exportaciones documentales deben limitarse a informacion necesaria para su finalidad. |
| RNF-062 | La aplicacion debe evitar exponer datos personales innecesarios en listados o respuestas publicas. |

### 7.16 Recuperabilidad y resiliencia

| Codigo | Requisito |
| --- | --- |
| RNF-063 | El sistema debe poder recuperar su estado funcional basico tras reinicios de servicios. |
| RNF-064 | Las entidades persistidas no deben depender de memoria temporal para su reconstruccion funcional. |
| RNF-065 | Los procesos asincronos deben dejar informacion suficiente para poder reanudar o revisar incidencias. |
| RNF-066 | La arquitectura debe facilitar estrategias futuras de backup y restauracion. |

### 7.17 Gobierno del dato

| Codigo | Requisito |
| --- | --- |
| RNF-067 | Los datos maestros deben mantenerse con definiciones coherentes entre backend, frontend y documentacion. |
| RNF-068 | Los campos de negocio criticos deben tener una semantica clara y estable. |
| RNF-069 | Los estados del sistema deben tener un significado funcional documentado. |
| RNF-070 | Las relaciones entre entidades principales deben poder explicarse y trazarse documentalmente. |

### 7.18 Mantenibilidad del frontend

| Codigo | Requisito |
| --- | --- |
| RNF-071 | El frontend debe organizarse por modulos funcionales reconocibles. |
| RNF-072 | La interfaz debe reutilizar componentes comunes cuando el patron visual sea equivalente. |
| RNF-073 | Los formularios complejos deben evitar duplicidad innecesaria de logica. |
| RNF-074 | La arquitectura del frontend debe facilitar nuevas pantallas sin rehacer la navegacion base. |

### 7.19 Mantenibilidad del backend

| Codigo | Requisito |
| --- | --- |
| RNF-075 | El backend debe separar modelos, serializers, viewsets y logica auxiliar de forma entendible. |
| RNF-076 | Los permisos personalizados deben ser localizables y reutilizables. |
| RNF-077 | Las utilidades de dominio deben concentrar reglas repetidas fuera del viewset cuando aplique. |
| RNF-078 | La organizacion por apps debe corresponder con dominios funcionales reales del negocio. |

### 7.20 Calidad de integracion

| Codigo | Requisito |
| --- | --- |
| RNF-079 | Las integraciones externas deben quedar documentadas con su finalidad, configuracion y riesgos. |
| RNF-080 | El proyecto debe permitir identificar con facilidad que partes del flujo dependen de terceros. |
| RNF-081 | El sistema debe registrar por logging cuando una integracion esperada no se aplica. |
| RNF-082 | Las integraciones documentales o de comunicacion deben poder evolucionar sin reescribir el sistema completo. |

### 7.21 Coherencia de experiencia

| Codigo | Requisito |
| --- | --- |
| RNF-083 | La aplicacion debe mantener una gramatica visual coherente entre modulos. |
| RNF-084 | Las acciones primarias, secundarias y destructivas deben distinguirse visualmente. |
| RNF-085 | Los estados vacios deben ser consistentes entre listados. |
| RNF-086 | La experiencia movil debe recibir especial atencion en modulos operativos. |

### 7.22 Capacidad de demostracion academica

| Codigo | Requisito |
| --- | --- |
| RNF-087 | El proyecto debe poder poblarse con datos demo suficientes para una defensa funcional. |
| RNF-088 | La documentacion debe permitir explicar el sistema a un lector no involucrado en su desarrollo. |
| RNF-089 | Las capturas, PDFs y flujos deben ser reproducibles con un entorno controlado. |
| RNF-090 | El conjunto documental debe poder reutilizarse como base de memoria final de TFG. |

## 8. Requisitos de interfaz

| Codigo | Requisito |
| --- | --- |
| RINT-001 | El sistema debe ofrecer una interfaz diferenciada por rol. |
| RINT-002 | La pantalla de detalle de ruta debe centrarse en consulta y planificacion. |
| RINT-003 | La pantalla de ejecucion de ruta debe centrarse en operacion y mapa. |
| RINT-004 | Los formularios de ventas deben mostrar una sola fecha operativa: fecha de factura. |
| RINT-005 | La configuracion de empresa debe organizarse en secciones independientes. |
| RINT-006 | Los contadores de los listados deben poder recogerse en movil cuando sea necesario. |
| RINT-007 | Las tablas o bloques extensos deben degradar de forma usable en pantallas pequenas. |
| RINT-008 | Las badges de estado deben mantener contraste y legibilidad en movil. |

## 9. Requisitos de integracion externa

| Codigo | Requisito |
| --- | --- |
| RIE-001 | El sistema debe poder usar Google Maps Platform para geocodificacion de clientes. |
| RIE-002 | El sistema debe poder usar Google Directions para optimizar el orden de paradas. |
| RIE-003 | El sistema debe poder abrir navegacion externa de Google Maps desde frontend. |
| RIE-004 | El sistema debe poder usar Gmail API para correos de acceso y notificaciones. |
| RIE-005 | El sistema debe poder generar facturas PDF con WeasyPrint. |
| RIE-006 | La ausencia de configuracion de una integracion opcional no debe bloquear la operacion base. |

## 10. Requisitos de seguridad y trazabilidad

| Codigo | Requisito |
| --- | --- |
| RSEG-001 | El owner debe ser el unico rol con acceso a compradores y ventas. |
| RSEG-002 | El worker no debe poder crear owners desde frontend. |
| RSEG-003 | El client solo debe ver sus solicitudes y recogidas. |
| RSEG-004 | Las acciones criticas deben dejar logging suficiente. |
| RSEG-005 | Las solicitudes deben registrar resolucion manual, automatica o por cliente. |
| RSEG-006 | Las recogidas deben reflejar estados coherentes con la operacion real. |
| RSEG-007 | Las facturas deben quedar asociadas a la venta que las origina. |

## 11. Requisitos operativos, de despliegue y calidad

| Codigo | Requisito |
| --- | --- |
| ROPS-001 | El entorno local debe poder levantarse con Docker Compose. |
| ROPS-002 | El backend debe depender de PostgreSQL/PostGIS para campos geoespaciales. |
| ROPS-003 | Redis debe estar disponible para broker y backend de Celery cuando se usen tareas asincronas. |
| ROPS-004 | La documentacion debe recoger variables de entorno relevantes. |
| ROPS-005 | La documentacion debe incluir guia de testing y mapa documental. |
| ROPS-006 | Debe existir una base de fixtures para poblar entornos demo. |
| ROPS-007 | El proyecto debe incluir una estructura de logs coherente para depuracion. |
| ROPS-008 | El entorno debe contemplar dependencias del sistema necesarias para WeasyPrint. |
| ROPS-009 | La carga de fixtures debe permitir demostrar el sistema en defensa o revision funcional. |
| ROPS-010 | El proyecto debe poder ejecutarse sin necesidad de modificar codigo para ajustar valores de empresa. |
| ROPS-011 | Debe existir una forma clara de validar la salud minima del backend y del frontend. |
| ROPS-012 | La estrategia de testing debe poder ejecutarse de forma documentada en entornos reproducibles. |

## 12. Requisitos de calidad del software

| Codigo | Requisito |
| --- | --- |
| RCAL-001 | El sistema debe ofrecer una separacion razonable entre responsabilidad funcional y presentacion. |
| RCAL-002 | El codigo debe ser suficientemente legible para facilitar mantenimiento academico y profesional. |
| RCAL-003 | Las decisiones de negocio relevantes deben estar documentadas. |
| RCAL-004 | Los nombres de entidades, endpoints y conceptos deben mantenerse consistentes en todo el proyecto. |
| RCAL-005 | Los cambios funcionales significativos deben reflejarse tambien en la documentacion. |
| RCAL-006 | Los modulos principales deben poder revisarse de forma independiente gracias a la modularidad del proyecto. |
| RCAL-007 | La aplicacion debe evitar comportamientos silenciosos que dificulten la depuracion de errores de negocio. |
| RCAL-008 | Las integraciones externas deben encapsularse de forma que su impacto sea entendible y mantenible. |
| RCAL-009 | El sistema debe mantener una relacion coherente entre documentacion, implementacion y testing. |
| RCAL-010 | Las decisiones de arquitectura deben poder justificarse con argumentos tecnicos y funcionales. |
| RCAL-011 | Los contratos de API deben mantenerse consistentes con los serializadores y el frontend. |
| RCAL-012 | El proyecto debe evitar deuda tecnica evidente en campos, estados o flujos ya consolidados. |
| RCAL-013 | Las correcciones funcionales relevantes deben venir acompanadas de actualizacion documental cuando corresponda. |
| RCAL-014 | La estructura general del proyecto debe facilitar revision, defensa y mantenimiento posterior. |

## 13. Priorizacion de requisitos

### 13.1 Requisitos imprescindibles

Se consideran imprescindibles para el valor actual del proyecto:

- gestion de clientes, trabajadores, camiones y zonas
- generacion semanal de rutas
- ejecucion diaria
- recogidas con medicion posterior
- configuracion global de empresa
- compradores, ventas y facturas
- estadisticas economicas basicas

### 13.2 Requisitos deseables pero no bloqueantes

- mayor cobertura E2E
- optimizacion mas avanzada de rutas
- integraciones contables externas
- analitica mas profunda

### 13.3 Requisitos estrategicos

Tambien se consideran estrategicos, aunque no todos sean imprescindibles para un MVP:

- trazabilidad fuerte de solicitudes y recogidas
- configuracion editable de empresa
- documentacion academica reutilizable
- testing modular en backend y frontend
- tolerancia a integraciones opcionales

## 14. Criterios globales de aceptacion

Se considerara que GreenPath cumple el bloque de requisitos cuando:

- el owner pueda configurar, planificar, vender y analizar
- el worker pueda operar rutas de forma usable
- el client pueda colaborar con la estimacion previa
- las rutas puedan generarse y ejecutarse sin incoherencias criticas
- las recogidas facturables computen correctamente en costes
- las ventas computen correctamente como ingresos
- el sistema disponga de documentacion suficiente para mantenimiento y defensa academica

## 15. Matriz resumida de trazabilidad

| Bloque de requisitos | Documento de apoyo principal |
| --- | --- |
| Negocio y procesos | `docs/FUNCIONAL.md` |
| API y contratos | `docs/API.md` |
| Arquitectura y stack | `docs/ARQUITECTURA_TECNICA.md` |
| Integraciones externas | `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md` |
| Planificacion y costes | `docs/PLANIFICACION_Y_COSTES.md` |
| Testing y validacion | `docs/TESTING.md` |
| Flujo de rutas | `docs/ROUTE_FLOW.md` |

## 16. Relacion con otros documentos

Este documento debe leerse junto con:

- `docs/FUNCIONAL.md`
- `docs/API.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/PLANIFICACION_Y_COSTES.md`
- `docs/TESTING.md`

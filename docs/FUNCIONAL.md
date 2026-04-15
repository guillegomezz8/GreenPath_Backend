# Documento Funcional GreenPath

Fecha de revision: 2026-04-14
Version funcional: 1.4

## 1. Proposito del documento

Este documento describe el funcionamiento real de GreenPath desde el punto de vista de negocio, operacion y gestion.
Su objetivo es servir como referencia comun para:

- entender que problema resuelve la plataforma
- delimitar el alcance funcional actual
- identificar que actores intervienen en cada proceso
- describir los flujos principales del negocio
- fijar las reglas funcionales que condicionan el comportamiento del sistema
- apoyar tareas de mantenimiento, evolucion, defensa y documentacion academica

Este documento no sustituye a la documentacion tecnica ni a la documentacion de API.
Su foco principal es explicar que hace el sistema, para quien lo hace, por que aporta valor y bajo que reglas debe operar.

## 2. Resumen ejecutivo

GreenPath es una plataforma para gestionar de forma unificada la operacion de una empresa dedicada a la recogida de aceite usado y a su posterior venta.

El sistema cubre el ciclo funcional principal del negocio:

1. configuracion de empresa y datos maestros
2. definicion geografica de zonas y rutas plantilla
3. generacion semanal de jornadas y paradas
4. solicitud previa de litros al cliente cuando aplica
5. ejecucion diaria de la ruta en calle
6. medicion posterior en nave y consolidacion economica de la recogida
7. registro de ventas a compradores
8. generacion de facturas PDF
9. calculo de costes, ingresos y beneficio neto

Por tanto, GreenPath no se limita a almacenar recogidas: articula una cadena completa de planificacion, ejecucion, trazabilidad y analitica economica.

## 3. Contexto y problema de negocio

El negocio al que da soporte GreenPath presenta varios retos funcionales simultaneos:

- los clientes se distribuyen geograficamente y deben agruparse por zonas
- las rutas no son fijas cada dia, sino que se generan a partir de una plantilla y de reglas semanales
- la cantidad real de aceite no siempre se conoce antes de la visita
- parte de la operacion sucede en calle y parte en nave
- el coste de recogida no es identico al ingreso posterior por venta
- la empresa necesita diferenciar entre operacion, economia y documentacion fiscal

Sin una plataforma unificada, estas tareas suelen quedar dispersas entre hojas de calculo, mensajes informales, llamadas, mapas externos y documentos sueltos.

GreenPath reduce esa fragmentacion mediante una unica plataforma capaz de conectar:

- geografia
- operacion diaria
- historico de recogidas
- configuracion fiscal
- ventas y facturacion
- estadisticas de negocio

## 4. Objetivos funcionales del sistema

Los objetivos funcionales principales de GreenPath son:

- centralizar en una sola plataforma los datos maestros del negocio
- permitir planificar rutas semanales a partir de zonas y frecuencia de clientes
- soportar una ejecucion diaria clara, usable y orientada a movilidad
- permitir al cliente informar litros antes de la recogida cuando sea necesario
- consolidar litros medidos y deducciones en nave
- diferenciar claramente entre coste operativo e ingreso comercial
- emitir facturas PDF de venta con datos fiscales configurables
- ofrecer visibilidad ejecutiva del estado operativo y economico del negocio

## 5. Beneficios funcionales esperados

### 5.1 Beneficios operativos

- menos trabajo manual en la generacion de rutas
- menos incertidumbre en la preparacion diaria
- mejor trazabilidad sobre que se recogio, cuando y por quien
- menor dependencia de herramientas externas desconectadas entre si

### 5.2 Beneficios economicos

- mejor visibilidad del coste real de las recogidas
- diferenciacion entre recogidas que computan y las que no
- registro estructurado de ventas
- calculo del beneficio neto del negocio

### 5.3 Beneficios de gestion

- datos fiscales de empresa editables sin tocar codigo
- historico funcional por cliente, trabajador y recogida
- documentacion de venta descargable y regenerable
- base mas solida para auditar, defender o evolucionar el sistema

## 6. Alcance funcional actual

Actualmente GreenPath cubre las siguientes areas:

- autenticacion y acceso por rol
- gestion de empresas, trabajadores, clientes y camiones
- definicion de zonas de recogida sobre mapa
- configuracion de rutas plantilla y zonas por dia
- generacion semanal de rutas operativas
- ejecucion diaria de paradas y cierre de jornada
- control operativo simplificado por capacidad con retorno implicito al hub
- solicitudes de estimacion de litros al cliente
- autoestimacion con Celery cuando el cliente no responde a tiempo
- registro de recogidas, medicion en nave y deducciones
- control economico basico de recogidas mediante precio por litro
- marca de recogida facturable o no facturable
- gestion interna de compradores
- gestion de ventas
- generacion de facturas PDF de venta
- configuracion fiscal y bancaria por empresa
- dashboard y estadisticas operativas y economicas
- perfil de usuario y cambio de contrasena

## 7. Fuera de alcance actual

Aunque la plataforma cubre una parte amplia del proceso, hay elementos que hoy no forman parte del alcance funcional cerrado:

- contabilidad oficial o integracion contable externa
- conciliacion bancaria automatica
- firma electronica de facturas
- portal de compradores
- reparto multi-vehiculo automatico para una misma ruta
- persistencia avanzada de subviajes, descargas y retornos reales al hub durante una jornada
- simulacion avanzada de optimizacion con restricciones complejas
- auditoria legal avanzada con versionado documental completo
- facturacion recurrente o por lotes
- motor avanzado de planificacion con multiples criterios empresariales configurables

## 8. Principios funcionales del sistema

### 8.1 Operacion por empresa

La mayoria de entidades funcionales viven dentro del contexto de una empresa.
Esto afecta a permisos, consultas, configuracion, rutas, compradores, ventas y estadisticas.

### 8.2 Separacion entre planificacion y ejecucion

GreenPath distingue claramente entre:

- configuracion de ruta plantilla
- semana operativa generada
- ejecucion diaria de una jornada concreta

Esto permite regenerar planificacion sin confundirla con datos ya operados.

### 8.3 Trazabilidad por encima del automatismo

El sistema automatiza tareas como:

- generacion de paradas
- optimizacion con Google
- creacion de solicitudes
- autoestimacion de litros
- generacion de factura PDF

Pero preserva la trazabilidad de:

- quien respondio una solicitud
- quien la cerro manualmente
- quien registro una recogida
- quien modifico los datos finales
- que registros computan economicamente y cuales no

### 8.4 Diferenciacion entre operacion y economia

No toda recogida debe necesariamente computar en resultados economicos.
Por eso existe la marca `billable` en `Collection`.

### 8.5 Configuracion editable

Los valores operativos y fiscales relevantes no deben quedar fijos en codigo.
La empresa puede ajustar desde la plataforma:

- precio global por litro
- hub operativo
- razon social y CIF
- direccion fiscal
- datos bancarios
- codigo LER
- pie de factura

### 8.6 Enfoque mobile-first en la operacion

Las pantallas de rutas y recogidas se usan en escenarios de movilidad.
Por ello, una parte relevante del diseno funcional prioriza:

- acciones claras
- modales usables en movil
- accesos rapidos
- tablas adaptadas a tarjetas en pantallas pequenas

### 8.7 Control operativo por capacidad en version simplificada

GreenPath incorpora una `v1` de control operativo por capacidad diaria.

En esta version:

- la jornada diaria sigue siendo una unica entidad funcional
- el sistema puede dividirla internamente en varios bloques de trabajo por capacidad
- si la carga prevista supera la capacidad diaria, se comunica que la ruta debe volver a nave antes de continuar
- esta division se usa en la vista operativa y en la exportacion de navegacion
- la segmentacion queda como logica interna de soporte y no como un elemento tecnico que deba exponerse en bruto al usuario final

Este enfoque cubre la necesidad principal del negocio sin introducir todavia nuevas entidades persistentes para viajes, descargas o retornos reales.

## 9. Supuestos funcionales y dependencias

El sistema parte de varios supuestos de negocio:

- cada empresa trabaja con su propio conjunto de clientes, trabajadores, camiones, compradores y ventas
- una ruta plantilla tiene un unico trabajador asignado en el modelo actual
- una semana operativa se genera a partir de zonas y reglas de frecuencia
- la empresa puede necesitar pedir litros al cliente antes de la recogida
- la medicion final y las deducciones se consolidan posteriormente
- la operacion en calle trabaja con carga prevista, no con medicion final consolidada
- una misma jornada puede implicar varios tramos y retornos a nave si la capacidad prevista se supera
- las ventas representan ingresos y las recogidas confirmadas facturables representan coste

Ademas, ciertas partes del flujo dependen de integraciones opcionales:

- Google Maps Platform para geocodificacion y optimizacion
- Gmail API para determinadas notificaciones por correo
- Celery y Redis para tareas asincronas

Cuando alguna de estas integraciones no esta disponible, el sistema debe degradar de forma controlada y continuar operando siempre que el caso de uso lo permita.

## 10. Actores del sistema

### 10.1 Owner

Es el rol con capacidad de configuracion, supervision y control del negocio.
Sus responsabilidades principales son:

- crear y mantener datos maestros
- configurar rutas, zonas y semanas operativas
- supervisar la ejecucion diaria
- editar recogidas y mediciones
- marcar recogidas como facturables o no facturables
- gestionar compradores
- registrar ventas y regenerar facturas
- configurar datos fiscales de la empresa
- consultar estadisticas globales

### 10.2 Worker

Es el rol orientado a la operacion diaria.
Sus responsabilidades principales son:

- consultar las rutas que le corresponden
- ejecutar la jornada diaria
- registrar la recogida fisica en cada parada
- cerrar o dejar parcial la jornada cuando proceda
- consultar datos operativos de su empresa segun permisos
- registrar manualmente litros de una solicitud cuando proceda

### 10.3 Client

Es el rol externo asociado a un cliente recogido por la empresa.
Su experiencia se limita a:

- consultar sus solicitudes abiertas
- responder litros antes de la expiracion
- consultar su historial de recogidas
- consultar y actualizar su perfil

### 10.4 Buyer

El comprador no es un usuario del sistema.
Es una entidad interna del negocio usada exclusivamente para:

- guardar datos fiscales del destinatario
- reutilizar esos datos al crear una venta
- emitir facturas PDF con informacion coherente

## 11. Matriz funcional de permisos

### 11.1 Owner

Puede acceder a:

- dashboard completo
- clientes
- trabajadores
- camiones
- zonas
- rutas
- recogidas
- compradores
- ventas
- configuracion
- estadisticas
- admin Django si ademas tiene permisos administrativos

Puede ejecutar acciones sensibles:

- generar semana operativa
- editar zonas por dia
- editar recogidas y ventas
- borrar registros permitidos
- regenerar facturas PDF
- modificar configuracion fiscal y operativa

### 11.2 Worker

Puede acceder a:

- rutas
- ejecucion diaria
- recogidas de su contexto
- perfil propio

No puede acceder a:

- compradores
- ventas
- configuracion fiscal
- generacion de semana
- mantenimiento maestro reservado a owner

### 11.3 Client

Puede acceder a:

- solicitudes de recogida propias
- historial de recogidas propio
- perfil propio

No puede acceder a:

- configuracion de empresa
- rutas internas
- compradores
- ventas
- estadisticas globales
- operacion interna de recogidas

## 12. Mapa funcional de entidades

### 12.1 Empresa

Representa la entidad operadora.
Agrupa el resto de informacion relevante del negocio.

### 12.2 CompanySettings

Recoge la configuracion global de la empresa.
Hoy concentra:

- `default_price_per_liter`
- datos fiscales de emisor para facturas
- datos bancarios
- codigo LER
- pie de factura

Es una pieza transversal que afecta tanto a recogidas como a facturacion.

### 12.3 CompanyHub

Representa la base o nave desde la que se entiende la operacion de ruta.
Se usa para:

- visualizar origen operativo
- optimizar con Google Directions cuando existe localizacion valida

### 12.4 Cliente

Es el punto de recogida habitual.
Guarda identidad, direccion, frecuencia de recogida y geolocalizacion.
La localizacion es relevante para la inclusion automatica en rutas generadas.

### 12.5 Trabajador

Representa al operario o conductor de la empresa.
Se relaciona con una empresa y puede quedar asignado a una ruta.

### 12.6 Camion

Representa el vehiculo operativo.
Se puede asociar a un trabajador.
Su capacidad puede influir como capacidad por defecto de una ruta diaria cuando aplica.

### 12.7 Zona

Es un poligono geografico de cobertura.
Las zonas se usan para seleccionar automaticamente clientes durante la generacion semanal.

### 12.8 Ruta

Es la plantilla operativa de una ruta.
Define:

- nombre
- empresa
- trabajador asignado
- rango de vigencia
- inicio y fin de semana operativa

### 12.9 RouteZoneDay

Relaciona una ruta con una o varias zonas en un dia concreto de semana.
Es la base de la planificacion semanal automatica.

### 12.10 RouteDay

Es la instancia diaria generada de una ruta plantilla para una fecha concreta.
Tiene estado, capacidad diaria e hitos reales de inicio y fin.

### 12.11 RouteDayClient

Es una parada concreta de cliente dentro de una jornada.
Guarda el orden planificado de recogida.

### 12.12 CollectionRequest

Es la solicitud de litros dirigida al cliente antes de la recogida.
Permite pedir una estimacion o confirmacion previa y, si no llega respuesta, deja camino a la autoestimacion.

### 12.13 Collection

Es la recogida ejecutada.
Concentra:

- cliente
- trabajador
- fecha
- envases
- litros medidos
- deducciones
- litros netos
- precio por litro
- total economico
- estado operativo
- marca de facturable

### 12.14 Buyer

Es el comprador interno para el modulo de ventas.
Guarda sus datos fiscales y de contacto.

### 12.15 Sale

Es la operacion de venta.
Concentra:

- comprador
- numero de factura manual
- fecha de factura
- descripcion del producto o servicio
- cantidad y unidad
- precio unitario
- subtotal
- IVA
- total
- PDF asociado

## 13. Mapa funcional por modulo

### 13.1 Modulo de clientes

#### Objetivo

Mantener el maestro de puntos de recogida y su informacion operativa.

#### Funcionalidades

- alta, edicion y baja logica
- registro de datos de contacto
- configuracion de frecuencia de recogida
- geocodificacion automatica a partir de direccion
- consulta de historial de recogidas
- consulta de total facturable historico

#### Reglas de negocio

- un cliente necesita localizacion valida para entrar automaticamente en una ruta generada por zonas
- la frecuencia de recogida condiciona cuando vuelve a ser elegible en generacion semanal
- el historial economico del cliente solo toma recogidas confirmadas y facturables

### 13.2 Modulo de trabajadores

#### Objetivo

Gestionar el personal operativo y su relacion con empresa, rutas y recogidas.

#### Funcionalidades

- alta, edicion y activacion o desactivacion
- consulta de historial de recogidas
- asignacion a rutas
- asociacion con camion cuando aplique

#### Reglas de negocio

- un trabajador solo puede operar dentro de su empresa
- los importes agregados del trabajador se calculan solo sobre recogidas confirmadas y facturables
- desde el flujo normal del frontend solo se crean trabajadores operativos con rol `worker`
- la creacion o mantenimiento de owners o administradores avanzados queda fuera del flujo operativo normal y se recomienda realizarla desde Django Admin

### 13.3 Modulo de camiones

#### Objetivo

Gestionar la flota de vehiculos del negocio.

#### Funcionalidades

- alta, edicion y consulta
- asignacion a conductor
- consulta de estado operativo

#### Reglas de negocio

- un camion no debe cruzar empresas
- la capacidad del camion puede usarse como referencia de capacidad por defecto de una ruta diaria

### 13.4 Modulo de zonas

#### Objetivo

Modelar la cobertura geografica de recogida.

#### Funcionalidades

- creacion y edicion de poligonos
- representacion en mapa
- vinculacion posterior a rutas por dia de semana

#### Reglas de negocio

- las zonas deben ser coherentes geograficamente para que la seleccion espacial de clientes funcione correctamente
- solapes y geometrias pobres degradan la planificacion automatica

### 13.5 Modulo de rutas

#### Objetivo

Planificar y supervisar la operacion semanal.

#### Funcionalidades

- crear rutas plantilla
- asignar trabajador a la ruta
- definir rango semanal operativo
- configurar zonas por dia (`RouteZoneDay`)
- consultar detalle semanal
- lanzar generacion operativa

#### Reglas de negocio

- la ruta trabaja con un solo trabajador asignado en el modelo actual
- los dias visibles y configurables deben respetar `week_start` y `week_end`
- el detalle de ruta se orienta a planificacion, no a operacion diaria completa

### 13.6 Modulo de generacion semanal

#### Objetivo

Construir la semana operativa a partir de una ruta plantilla.

#### Entrada funcional

- ruta plantilla
- fecha de inicio de semana
- capacidad global o capacidades por dia
- opcion de regenerar
- opcion de autoestimar sin esperar contacto
- maximo de clientes por dia

#### Salida funcional

- `RouteDay` creados o reutilizados
- `RouteDayClient` generados y ordenados
- `CollectionRequest` creados o actualizados
- tareas Celery programadas

#### Reglas de negocio clave

- la operacion es idempotente
- solo owner puede ejecutar `generate-week`
- `regenerate=true` solo se permite si toda la semana sigue siendo editable
- si `regenerate=false`, los dias ya operados se preservan
- se respetan frecuencia, empresa, capacidad y limite maximo de clientes por dia
- el criterio funcional actual usa `10` clientes por jornada como valor por defecto
- la optimizacion con Google es opcional y no bloquea la generacion si falla o falta API key

### 13.7 Modulo de solicitudes de recogida

#### Objetivo

Solicitar al cliente una estimacion o confirmacion previa de litros.

#### Funcionalidades

- creacion automatica desde la generacion semanal
- expiracion automatica
- respuesta del cliente
- carga manual por owner o worker
- autoestimacion por tarea asincrona
- envio de correo de notificacion

#### Estados funcionales

- `PENDING`
- `AUTO_ESTIMATED`
- `ANSWERED`
- `MANUAL`

#### Reglas de negocio

- `expires_at` se calcula como inicio de la jornada menos 36 horas
- si el cliente responde a tiempo, prevalece su valor final
- si no responde, el sistema puede autoestimar por historico o por capacidad del envase
- owner y worker pueden resolver manualmente una solicitud

### 13.8 Modulo de ejecucion de ruta

#### Objetivo

Permitir que owner o worker operen la jornada diaria de forma controlada.

#### Funcionalidades

- iniciar `RouteDay`
- visualizar paradas del dia
- abrir navegacion en Google
- registrar parada
- finalizar jornada
- decidir cierre parcial o cancelacion si quedan pendientes
- fijar por defecto la semana operativa actual en la experiencia de ejecucion

#### Reglas de negocio

- una jornada no puede iniciarse en cualquier estado
- una parada cancelada cuenta como procesada para cerrar la jornada
- si no quedan pendientes, el cierre correcto es `COMPLETED`
- si quedan pendientes, el cierre exige una decision explicita (`PARTIAL` o `CANCELED`)

### 13.9 Modulo de recogidas

#### Objetivo

Registrar y consolidar el resultado real de una recogida.

#### Funcionalidades

- alta manual de recogidas
- edicion posterior para medicion en nave
- gestion de envases
- deducciones por agua, residuo, mezcla u otros motivos
- calculo de litros netos
- calculo de importe
- marca de `facturable`

#### Estados funcionales

- `PENDING_MEASUREMENT`
- `CONFIRMED`
- `CANCELED`

#### Reglas de negocio

- al crear una recogida manual, si no se informa precio por litro, se toma el precio global de empresa
- al completar una parada desde ruta, la recogida nace con datos minimos y puede quedar pendiente de medicion
- una recogida no facturable sigue siendo visible y operativa, pero no entra en calculos economicos
- solo las recogidas confirmadas y facturables impactan en costes, totales del cliente y totales del trabajador

### 13.10 Modulo de compradores

#### Objetivo

Mantener el maestro interno de destinatarios de factura de venta.

#### Funcionalidades

- alta, edicion, detalle y listado
- datos fiscales completos
- filtros por ciudad, provincia y contacto

#### Reglas de negocio

- el comprador no accede a la plataforma
- el CIF o NIF es unico por empresa
- se expone direccion fiscal completa para facilitar facturacion

### 13.11 Modulo de ventas

#### Objetivo

Registrar operaciones de venta y reflejar los ingresos del negocio.

#### Funcionalidades

- alta, edicion, detalle y listado
- seleccion de comprador
- numero de factura manual
- fecha de factura
- descripcion, cantidad, unidad y precio unitario
- calculo automatico de subtotal, IVA y total
- descarga y regeneracion de PDF

#### Reglas de negocio

- acceso solo para owner
- `invoice_number` es manual y obligatorio
- `invoice_number` debe ser unico por empresa
- `invoice_date` es la unica fecha visible y funcional del modulo
- `sale_date` se sincroniza internamente con `invoice_date` para mantener compatibilidad del modelo
- el PDF siempre representa el estado actual de la venta y la configuracion fiscal de la empresa

### 13.12 Modulo de facturacion PDF

#### Objetivo

Emitir un documento de factura coherente y descargable a partir de una venta.

#### Funcionalidades

- generacion automatica del PDF
- regeneracion manual
- descarga desde detalle de venta
- uso de datos fiscales configurables
- uso de plantilla HTML y CSS renderizada con WeasyPrint

#### Reglas de negocio

- los datos del emisor se toman de `CompanySettings`
- los datos del destinatario se toman del `Buyer`
- el PDF no es un documento fijo en codigo: depende de la configuracion actual de empresa y de la venta

### 13.13 Modulo de configuracion de empresa

#### Objetivo

Centralizar ajustes operativos y fiscales que afectan a varios procesos.

#### Funcionalidades

- precio global por litro
- datos fiscales del emisor
- datos bancarios
- codigo LER
- pie de factura
- seleccion del hub en mapa

#### Reglas de negocio

- owner puede editar
- worker puede consultar segun endpoint, pero no modificar
- los cambios impactan en nuevas recogidas y nuevas facturas

### 13.14 Modulo de estadisticas

#### Objetivo

Ofrecer una vision sintetica del estado operativo y economico del negocio.

#### Funcionalidades

- KPIs globales para owner
- actividad reciente
- comparativas de volumen comprado y vendido
- resumen economico de costes, ingresos y beneficio
- acceso rapido a rutas operativas desde owner

#### Reglas de negocio

- el bloque economico separa costes e ingresos
- el coste viene de recogidas `CONFIRMED` y `billable=true`
- el ingreso viene de ventas registradas
- el beneficio neto se calcula como ingresos menos costes

### 13.15 Modulo de perfil

#### Objetivo

Permitir que cada usuario gestione sus datos basicos y su acceso.

#### Funcionalidades

- consulta de datos personales
- actualizacion de email y telefono cuando aplica
- cambio de contrasena
- actualizacion de imagen en perfiles que lo soportan

#### Reglas de negocio

- cada usuario solo puede modificar su propio perfil
- el contenido visible del perfil depende del rol y del tipo de perfil asociado

## 14. Procesos funcionales de extremo a extremo

### 14.1 Preparacion inicial del sistema

1. Se crea la empresa y su owner.
2. Se crean trabajadores y clientes.
3. Se crean camiones si aplica.
4. Se delimitan zonas de recogida.
5. Se configura el hub de empresa.
6. Se define el precio global por litro.
7. Se cargan datos fiscales y bancarios de la empresa.
8. Se crean rutas plantilla y se asignan zonas por dia.

Resultado esperado:

- el sistema queda listo para generar semanas operativas y posteriormente emitir facturas de venta

### 14.2 Generacion semanal operativa

1. El owner selecciona una ruta.
2. Elige una semana operativa.
3. Informa capacidad global o capacidad por dias.
4. Decide si quiere regenerar o no.
5. El backend valida que la semana este en rango y que la operacion sea legal.
6. Se crean o reutilizan `RouteDay`.
7. Para cada dia se buscan clientes dentro de las zonas del weekday correspondiente.
8. Se filtran por frecuencia y planificacion previa de la misma empresa.
9. Se respeta el maximo de clientes por dia.
10. Se respeta la capacidad diaria.
11. Se ordenan las paradas.
12. Si hay configuracion de Google y datos suficientes, se optimiza el orden.
13. Se crea una `CollectionRequest` por parada.
14. Se agenda la autoestimacion futura.
15. Se registra trazabilidad y se devuelve el resumen de la semana generada.

Durante esta fase, el sistema deja preparada tambien la base operativa de la ejecucion:

- calcula una carga prevista por parada
- detecta si la jornada cabe en un solo bloque o en varios retornos al hub
- deja lista la informacion necesaria para representar futuros retornos al hub

### 14.3 Notificacion al cliente y respuesta previa

1. Se crea la `CollectionRequest`.
2. El sistema envia correo al cliente cuando la configuracion de Gmail esta disponible.
3. El cliente entra al portal y consulta sus solicitudes.
4. Si responde antes de la expiracion, la solicitud pasa a `ANSWERED`.
5. Si owner o worker intervienen, pasa a `MANUAL`.
6. Si no llega respuesta a tiempo, Celery puede moverla a `AUTO_ESTIMATED`.

### 14.4 Ejecucion diaria de ruta

1. Owner o worker entra en la pantalla `Realizar ruta`.
2. Selecciona la jornada concreta.
3. Inicia la jornada.
4. Consulta el orden de parada, el mapa y la siguiente parada sugerida.
5. El sistema mantiene internamente la logica de capacidad y retornos al hub cuando aplica.
6. Propone por defecto la siguiente parada pendiente correcta.
7. Registra cada parada con tipo y numero de envases.
8. El sistema crea o actualiza la `Collection` asociada.
9. Si una parada se cancela, queda gestionada pero no suma carga operativa.
10. Al final del dia, el usuario intenta finalizar.
11. Si quedan pendientes, debe decidir entre cierre parcial o cancelacion.
12. Si no quedan pendientes, el dia termina como completado.

### 14.5 Medicion y cierre economico en nave

1. Una recogida registrada en calle puede quedar pendiente de medicion.
2. En nave se completan litros medidos, deducciones y motivo.
3. Se recalculan litros netos.
4. Se recalcula el importe total segun precio por litro.
5. Se decide si la recogida es facturable o no.
6. Solo si esta confirmada y facturable impacta en reporting economico.

### 14.6 Venta y facturacion

1. El owner mantiene previamente el maestro de compradores.
2. El owner crea una venta.
3. Introduce comprador, numero de factura, fecha de factura y concepto.
4. El backend calcula subtotal, IVA y total.
5. Se genera el PDF.
6. La venta se suma al bloque de ingresos del negocio.
7. El owner puede descargar o regenerar la factura cuando quiera.

## 15. Ciclo de vida funcional de los datos

### 15.1 Ciclo de vida de una recogida planificada

1. el cliente existe como maestro y tiene localizacion
2. una ruta plantilla define zonas para un dia concreto
3. la generacion semanal crea un `RouteDay`
4. se crea una parada `RouteDayClient`
5. se crea una `CollectionRequest`
6. el cliente responde o el sistema autoestima la solicitud
7. durante la ejecucion se registra la recogida
8. posteriormente se mide y se confirma en nave
9. si es facturable, entra en costes y estadisticas

### 15.2 Ciclo de vida de una venta

1. se registra o reutiliza un comprador
2. se crea la venta con numero de factura y fecha de factura
3. el backend recalcula importes
4. se genera el PDF
5. la venta pasa a computar como ingreso del negocio

### 15.3 Ciclo de vida de la configuracion fiscal

1. el owner actualiza datos fiscales y bancarios
2. el sistema guarda la configuracion por empresa
3. nuevas ventas y facturas consumen esos datos
4. si cambia la configuracion y se regenera una factura, el PDF reflejara el estado vigente segun el flujo actual

## 16. Reglas de negocio detalladas

### 16.1 Reglas de rutas y planificacion

- la semana operativa debe estar dentro del rango de la ruta
- la generacion semanal es idempotente
- la ruta usa un unico trabajador asignado en el modelo actual
- `regenerate=true` no puede destruir dias ya operados o con recogidas asociadas
- sin `regenerate`, los dias ya operados se preservan
- la inclusion de clientes depende de zona, frecuencia y empresa
- no se debe duplicar el mismo cliente dos veces en la misma semana
- `max_clients_per_day` se respeta antes de cerrar el dia
- `daily_capacity_liters` se aplica de forma estricta desde la primera parada

### 16.2 Reglas de Google Directions

- si no hay `GOOGLE_MAPS_API_KEY`, la generacion continua sin optimizacion
- si la empresa no tiene hub geolocalizado, tampoco se optimiza
- si la respuesta de Google es invalida, se conserva el orden actual
- el sistema deja trazas en logs indicando si la optimizacion se aplico o no

### 16.3 Reglas de solicitudes al cliente

- el correo solo se envia si la integracion Gmail esta correctamente configurada
- la fecha limite se calcula como inicio de jornada menos 36 horas
- el cliente solo puede responder mientras la solicitud no este expirada
- si la solicitud ya no esta en estado admitido, la respuesta queda bloqueada
- owner y worker pueden intervenir manualmente dentro de su empresa

### 16.4 Reglas de recogidas

- una recogida cancelada no se trata como confirmada ni como coste
- una recogida pendiente de medicion aun no consolida su impacto final
- una recogida confirmada puede seguir marcada como no facturable
- el historial de cliente y trabajador muestra tanto el estado operativo como la condicion de facturable o no facturable

### 16.5 Reglas de ventas y facturas

- el numero de factura no se autogenera: lo define el owner
- la unicidad se controla por empresa
- la fecha funcional de la venta es `invoice_date`
- subtotal, IVA y total no se toman del frontend como valores finales de confianza
- el backend recalcula importes para preservar coherencia

### 16.6 Reglas de estadisticas

- coste = suma de `Collection.total_price` de recogidas `CONFIRMED` y `billable=true`
- ingreso = suma de `Sale.total`
- beneficio neto = ingreso - coste
- volumen comprado = litros netos de recogidas que computan
- volumen vendido = cantidad registrada en ventas

### 16.7 Reglas de seguridad funcional

- un cliente solo puede consultar y responder sus propias solicitudes
- un cliente solo puede ver sus propias recogidas
- un worker opera dentro del ambito de su empresa y sus permisos funcionales
- compradores, ventas, configuracion y bloque economico quedan reservados a owner

## 17. Estados funcionales y significado

### 17.1 RouteDay

- `PLANNED`: jornada planificada aun no iniciada
- `IN_PROGRESS`: jornada iniciada y en curso
- `COMPLETED`: jornada cerrada sin pendientes
- `PARTIAL`: jornada cerrada con pendientes no ejecutadas
- `CANCELED`: jornada cancelada

### 17.2 CollectionRequest

- `PENDING`: pendiente de respuesta
- `AUTO_ESTIMATED`: resuelta por autoestimacion
- `ANSWERED`: respondida por el cliente
- `MANUAL`: resuelta manualmente por owner o worker

### 17.3 Collection

- `PENDING_MEASUREMENT`: operacion registrada pero pendiente de medicion final
- `CONFIRMED`: operacion medida y consolidada
- `CANCELED`: operacion anulada

## 18. Experiencia funcional por rol

### 18.1 Experiencia owner

El owner dispone de una experiencia de gestion completa.
Su recorrido habitual es:

- configurar empresa y datos fiscales
- mantener clientes, trabajadores, camiones y zonas
- generar semanas operativas
- revisar detalle de rutas
- ejecutar o supervisar jornadas
- revisar recogidas ya medidas
- mantener compradores
- registrar ventas
- descargar facturas
- revisar dashboard y estadisticas

### 18.2 Experiencia worker

El worker se enfoca en operar.
Su recorrido habitual es:

- consultar sus rutas
- abrir la ruta diaria
- iniciar la jornada
- recoger paradas
- cerrar la jornada
- revisar recogidas propias cuando proceda

### 18.3 Experiencia client

El cliente se enfoca en responder y consultar.
Su recorrido habitual es:

- entrar al sistema
- consultar solicitudes pendientes
- responder litros
- revisar historico de recogidas
- consultar y actualizar su perfil

## 19. Integraciones externas con impacto funcional

### 19.1 Google Maps and Directions

Se utiliza para:

- geocodificacion de direcciones de clientes
- optimizacion provisional del orden de paradas
- apertura de navegacion externa desde la operativa diaria

### 19.2 Gmail API

Se utiliza para:

- envio de credenciales iniciales
- envio de notificaciones operativas al cliente sobre solicitudes de estimacion

### 19.3 Celery y Redis

Se utilizan para:

- programar autoestimaciones de solicitudes
- ejecutar tareas diferidas relacionadas con vencimientos y notificaciones

### 19.4 WeasyPrint

Se utiliza para:

- generar las facturas PDF de venta a partir de plantillas HTML y CSS

## 20. Requisitos no funcionales con impacto funcional

### 20.1 Multiempresa

La plataforma debe aislar datos por empresa y evitar cruces indebidos entre usuarios y registros.

### 20.2 Responsive y uso en movilidad

La parte de rutas y recogidas se ha trabajado con enfoque mobile-first porque worker y owner pueden operar desde movil durante la jornada.

### 20.3 Tolerancia a integraciones opcionales

Si Google o Gmail no estan disponibles, el sistema debe degradar funcionalmente sin romper el flujo base siempre que el caso de uso lo permita.

### 20.4 Mantenibilidad funcional

Los valores de negocio que pueden variar se mueven a configuracion editable para reducir dependencia de cambios en codigo.

## 21. Indicadores funcionales del negocio

Los indicadores mas relevantes que hoy soporta GreenPath son:

- numero de clientes activos
- numero de trabajadores activos
- numero de rutas operativas
- numero de recogidas por estado
- litros netos recogidos
- total invertido en recogidas facturables
- total ingresado en ventas
- beneficio neto
- volumen comprado frente a volumen vendido
- actividad reciente

## 22. Riesgos y puntos de atencion funcional

- calidad de las coordenadas del cliente: si la geocodificacion falla, el cliente puede quedar fuera de planificacion automatica
- configuracion de zonas: zonas mal definidas generan planificaciones pobres o clientes no capturados
- dependencias externas: Google y Gmail requieren credenciales validas
- datos fiscales incompletos: una venta puede existir, pero la factura sera peor si la configuracion de empresa o comprador esta incompleta
- decision sobre `billable`: afecta directamente a margenes y reporting
- errores de operacion movil: una mala UX en campo afecta directamente al dato final

## 23. Escenarios de error relevantes

- generacion semanal sobre semana fuera de rango
- intento de regenerar una semana ya operada
- respuesta del cliente fuera de plazo
- recogida editada con datos de medicion inconsistentes
- venta con numero de factura duplicado en la misma empresa
- PDF no regenerable por falta de dependencias o datos invalidos
- cliente sin localizacion valida para planificacion geografica

## 24. Glosario

- Hub: nave o punto base de salida de la empresa
- Ruta plantilla: definicion base de una ruta reutilizable
- RouteDay: jornada diaria generada desde una ruta plantilla
- RouteDayClient: parada concreta dentro de una jornada
- CollectionRequest: solicitud previa de estimacion de litros
- Collection: recogida real ejecutada
- Billable: marca que determina si una recogida computa economicamente
- Buyer: comprador interno para modulo de ventas
- Sale: operacion de venta registrada en sistema
- Invoice PDF: factura de venta generada para una `Sale`

## 25. Requisitos funcionales resumidos

### 25.1 Requisitos de operacion

- el owner debe poder crear y mantener clientes, trabajadores, camiones, zonas y rutas
- el owner debe poder generar una semana operativa para una ruta plantilla
- el sistema debe crear jornadas (`RouteDay`) y paradas (`RouteDayClient`) de forma idempotente
- el sistema debe respetar la configuracion semanal de zonas y dias
- el sistema debe filtrar clientes por frecuencia y por planificacion previa de la misma empresa
- el sistema debe poder optimizar el orden de una jornada con Google cuando la integracion este disponible
- el worker debe poder iniciar, operar y finalizar la jornada diaria desde movil
- el cierre de jornada debe distinguir entre cierre completo, parcial y cancelado segun la operacion real
- la navegacion exportada debe salir del hub y volver al hub al cierre de la jornada

### 25.2 Requisitos de solicitud y estimacion

- el sistema debe crear una solicitud de estimacion asociada a cada parada planificada
- el cliente debe poder responder litros antes del vencimiento
- owner y worker deben poder intervenir manualmente una solicitud
- el sistema debe poder autoestimar cuando el cliente no responde dentro del plazo
- toda resolucion debe dejar trazabilidad del origen de la respuesta

### 25.3 Requisitos de recogidas

- una recogida debe poder registrarse manualmente o desde una parada de ruta
- una recogida debe poder quedar pendiente de medicion
- una recogida debe poder incorporar deducciones y motivo de deduccion
- una recogida debe poder marcarse como facturable o no facturable
- solo las recogidas confirmadas y facturables deben entrar en el resumen economico
- la operacion de ruta debe poder sugerir la siguiente parada pendiente correcta segun el plan operativo interno
- el sistema debe poder representar retornos al hub cuando la capacidad prevista diaria lo exija

### 25.4 Requisitos economicos

- el owner debe poder registrar compradores internos
- el owner debe poder registrar ventas con numero de factura manual
- cada venta debe generar un PDF descargable y regenerable
- la empresa debe poder editar sus datos fiscales y bancarios
- las estadisticas deben distinguir con claridad entre costes, ingresos y beneficio

## 26. Casos de uso prioritarios

### 26.1 Caso de uso: generar semana operativa

Actor principal:
- owner

Precondiciones:
- existe una ruta plantilla con zonas configuradas por dia
- la empresa tiene clientes georreferenciados dentro de las zonas

Resultado esperado:
- se crean o actualizan los `RouteDay` de la semana
- se crean las paradas candidatas respetando reglas de frecuencia
- se generan solicitudes para que el cliente informe litros o el sistema autoestime

### 26.2 Caso de uso: ejecutar una ruta diaria

Actor principal:
- worker

Precondiciones:
- existe una jornada generada
- el worker tiene acceso a la ruta asignada

Resultado esperado:
- el worker inicia la jornada
- consulta el mapa, la parada activa y la navegacion
- registra recogidas o cancelaciones
- finaliza la jornada dejando el estado correcto

### 26.3 Caso de uso: medir una recogida en nave

Actor principal:
- owner o worker con permisos

Precondiciones:
- existe una recogida registrada y pendiente de medicion

Resultado esperado:
- se informan litros finales
- se recalculan importes y deducciones
- la recogida queda confirmada o cancelada
- si es facturable, pasa a computar en resumen economico

### 26.4 Caso de uso: registrar una venta y emitir factura

Actor principal:
- owner

Precondiciones:
- existe un comprador dado de alta
- la empresa tiene configurados sus datos fiscales minimos

Resultado esperado:
- se crea una venta
- se asigna el numero de factura indicado por negocio
- se genera el PDF de factura
- la venta pasa a computar como ingreso en estadisticas

## 27. Criterios globales de aceptacion funcional

Para considerar el sistema funcionalmente coherente en una entrega, al menos debe cumplirse lo siguiente:

- un owner puede preparar el maestro de datos sin tocar codigo
- una ruta puede generarse, ejecutarse y cerrarse de extremo a extremo
- un cliente puede responder una solicitud antes de su expiracion
- una recogida puede medirse, confirmarse y quedar correctamente reflejada en detalle e historico
- una venta puede registrarse y emitir factura PDF con datos fiscales configurables
- las estadisticas muestran separadamente operacion y economia
- la experiencia movil permite operar rutas y recogidas sin depender de escritorio
- los modulos economicos y de configuracion quedan restringidos a owner

## 28. Matriz resumida de modulos por rol

### 28.1 Owner

Puede operar funcionalmente sobre:

- dashboard global
- clientes
- trabajadores
- camiones
- zonas
- rutas
- recogidas
- compradores
- ventas
- configuracion
- estadisticas

Puede ejecutar acciones criticas como:

- generar semana operativa
- editar configuracion fiscal
- marcar recogidas facturables
- medir y confirmar recogidas
- generar y regenerar facturas PDF

### 28.2 Worker

Puede operar funcionalmente sobre:

- rutas asignadas o visibles segun permisos
- ejecucion de jornada
- registro de recogidas desde ruta
- consulta de recogidas de su ambito
- perfil propio

No deberia operar sobre:

- compradores
- ventas
- configuracion fiscal
- generacion semanal de rutas

### 28.3 Client

Puede operar funcionalmente sobre:

- solicitudes abiertas
- respuesta de litros
- historico de recogidas
- perfil propio

No deberia operar sobre:

- maestros de empresa
- rutas internas
- configuracion
- estadisticas globales
- bloque economico interno

## 29. Documentacion complementaria

Para ampliar este documento conviene consultar:

- `README.md`
- `docs/INDICE_DOCUMENTACION.md`
- `docs/API.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/ROUTE_FLOW.md`
- `docs/REQUISITOS.md`
- `docs/CASOS_DE_USO.md`
- `docs/MANUAL_USUARIO.md`
- `docs/DESPLIEGUE_Y_OPERACION.md`
- `docs/BIBLIOGRAFIA_Y_FUENTES.md`

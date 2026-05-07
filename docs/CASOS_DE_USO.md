# Casos de Uso GreenPath

Fecha de revision: 2026-04-30

## 1. Objetivo del documento

Este documento describe los casos de uso principales del sistema GreenPath con un nivel de detalle mayor que el backlog de historias de usuario. Su objetivo es servir como puente entre:

- los requisitos formales del proyecto
- la documentacion funcional
- la explicacion academica del comportamiento del sistema

Cada caso de uso se expresa con:

- actor principal
- objetivo
- precondiciones
- flujo principal
- flujos alternativos o excepciones
- resultado esperado

La revision actual incorpora el alcance completo del TFG: gestion multiempresa, rutas con apoyo geografico, operacion movil, recogidas facturables, ventas, compradores, facturacion PDF bajo demanda, tareas asincronas e integraciones externas.

## 2. Actores considerados

| Actor | Descripcion |
| --- | --- |
| Owner | Usuario con control funcional y economico completo |
| Worker | Usuario operativo que ejecuta rutas y registra recogidas |
| Client | Usuario externo vinculado a un cliente |
| Sistema | Procesos automaticos del propio producto |

## 3. Casos de uso del owner

### CU-001. Crear cliente

**Actor principal:** Owner

**Objetivo:** dar de alta un nuevo cliente para futuras recogidas.

**Precondiciones:**

- el owner esta autenticado
- el owner pertenece a una empresa valida

**Flujo principal:**

1. el owner accede al modulo de clientes
2. abre la pantalla de alta
3. introduce datos de identificacion, contacto y direccion
4. el sistema valida la informacion
5. el sistema crea el usuario/cliente asociado
6. el sistema intenta geocodificar la direccion
7. el cliente queda disponible para operacion futura

**Flujos alternativos:**

- si la geocodificacion falla, el cliente se crea igualmente pero sin coordenadas
- si faltan campos obligatorios, el sistema devuelve errores de validacion

**Resultado esperado:**

- el cliente queda registrado y visible en listados y detalle

### CU-002. Crear trabajador

**Actor principal:** Owner

**Objetivo:** dar de alta un trabajador operativo en la empresa.

**Precondiciones:**

- el owner esta autenticado
- el owner tiene permisos de gestion de trabajadores

**Flujo principal:**

1. el owner accede al modulo de trabajadores
2. abre la pantalla de alta
3. introduce datos personales y operativos
4. el sistema valida la informacion
5. el sistema crea el trabajador
6. el sistema fuerza el rol a `worker`

**Flujos alternativos:**

- si el payload incluye cambios de rol no permitidos, el backend los ignora o rechaza segun el caso
- si se intenta crear un owner desde el front, el sistema no lo permite

**Resultado esperado:**

- el trabajador queda registrado como trabajador normal, no como owner

### CU-003. Crear zona de recogida

**Actor principal:** Owner

**Objetivo:** definir un area geografica de operacion.

**Precondiciones:**

- el owner esta autenticado
- el owner tiene acceso al modulo de zonas

**Flujo principal:**

1. el owner abre el modulo de zonas
2. dibuja o define el poligono correspondiente
3. introduce nombre y datos descriptivos
4. el sistema valida la geometria
5. la zona queda disponible para vincularse a rutas

**Resultado esperado:**

- existe una zona reutilizable en planificacion

### CU-004. Crear ruta plantilla

**Actor principal:** Owner

**Objetivo:** configurar una ruta recurrente de recogida.

**Precondiciones:**

- existen zonas y, si procede, trabajadores creados

**Flujo principal:**

1. el owner accede al modulo de rutas
2. crea una nueva ruta
3. define nombre, periodo y trabajador asignado
4. asigna zonas por dia de semana
5. guarda la ruta

**Resultado esperado:**

- la ruta queda lista para generar semanas operativas

### CU-005. Generar semana operativa

**Actor principal:** Owner

**Objetivo:** convertir una ruta plantilla en jornadas reales para una semana concreta.

**Precondiciones:**

- la ruta existe
- la ruta tiene zonas por dia
- el owner tiene permisos de generacion

**Flujo principal:**

1. el owner abre el detalle o listado de rutas
2. lanza el modal de `generate-week`
3. selecciona la semana
4. introduce capacidad global o capacidad por fecha
5. confirma la accion
6. el sistema crea o actualiza `RouteDay`
7. el sistema selecciona clientes por zona y frecuencia
8. el sistema crea paradas (`RouteDayClient`)
9. el sistema optimiza el orden si la integracion esta disponible
10. el sistema crea solicitudes de estimacion
11. el sistema deja preparado el plan operativo por capacidad para la ejecucion posterior

**Flujos alternativos:**

- si la semana ya existe y es editable, el sistema puede reutilizarla
- si `regenerate` no es valido por estado operativo previo, el sistema bloquea la accion
- si Google no esta disponible, se mantiene un orden secuencial

**Resultado esperado:**

- la semana queda generada y visible en la interfaz

### CU-005B. Ejecutar jornada con retorno implicito al hub

**Actor principal:** Worker

**Objetivo:** operar una jornada diaria entendiendo cuando la capacidad obliga a volver a nave antes de continuar.

**Precondiciones:**

- existe un `RouteDay` generado
- el usuario tiene permisos sobre esa ruta
- la empresa dispone de hub si quiere navegacion completa con retorno

**Flujo principal:**

1. el worker abre `RouteExecution`
2. selecciona una jornada operativa
3. el sistema muestra la siguiente parada sugerida, el mapa operativo y el contexto de retorno al hub cuando aplica
4. el usuario inicia la jornada si todavia no esta en curso
5. registra las paradas pendientes siguiendo la sugerencia operativa del sistema
6. si la jornada requiere mas de un tramo, el sistema comunica que tocara volver a nave antes de continuar
7. el usuario abre la navegacion externa si la necesita
8. cuando ya no quedan pendientes, finaliza la jornada

**Flujos alternativos:**

- si no existe hub, la jornada sigue siendo operable pero la navegacion externa puede no estar disponible
- si una parada se cancela, cuenta como gestionada pero no suma carga operativa
- si quedan pendientes al cerrar, el sistema exige decision entre `PARTIAL` y `CANCELED`

**Resultado esperado:**

- la operacion diaria refleja mejor la realidad de carga y retorno del vehiculo sin requerir una tabla extra de subviajes

### CU-006. Resolver manualmente una solicitud de recogida

**Actor principal:** Owner

**Objetivo:** introducir manualmente una estimacion cuando el cliente no la aporta o se decide intervenir.

**Precondiciones:**

- existe una `CollectionRequest`
- la solicitud sigue en un estado resoluble

**Flujo principal:**

1. el owner localiza la solicitud
2. introduce manualmente el valor de litros estimados
3. el sistema actualiza el estado y registra la autoria

**Resultado esperado:**

- la solicitud queda resuelta manualmente

### CU-007. Medir una recogida en nave

**Actor principal:** Owner

**Objetivo:** consolidar la recogida para su impacto economico real.

**Precondiciones:**

- existe una recogida registrada
- la recogida esta en estado pendiente de medicion o editable

**Flujo principal:**

1. el owner abre el detalle o la edicion de la recogida
2. introduce litros medidos
3. introduce deducciones si procede
4. revisa el precio por litro
5. marca si la recogida es facturable
6. guarda la informacion

**Flujos alternativos:**

- si la recogida no debe participar en economia, se marca como no facturable
- si se cancela, el sistema ajusta su estado y elimina impacto economico

**Resultado esperado:**

- la recogida queda lista para participar o no en el bloque economico

### CU-008. Crear comprador interno

**Actor principal:** Owner

**Objetivo:** registrar un comprador para futuras ventas.

**Precondiciones:**

- el owner tiene acceso al bloque economico

**Flujo principal:**

1. el owner accede al modulo de compradores
2. crea un nuevo registro
3. introduce datos fiscales y de contacto
4. guarda el comprador

**Resultado esperado:**

- el comprador queda disponible para asociarlo a ventas

### CU-009. Registrar venta y generar factura

**Actor principal:** Owner

**Objetivo:** registrar un ingreso comercial y emitir la factura asociada.

**Precondiciones:**

- existe un comprador interno
- la empresa tiene configurados sus datos de facturacion

**Flujo principal:**

1. el owner accede al modulo de ventas
2. crea una nueva venta
3. selecciona comprador
4. introduce numero de factura, fecha de factura, concepto, cantidad, unidad y precio; el formulario muestra como ayuda el numero de la ultima factura y la unidad inicial aparece como `kg`
5. si quiere reutilizar una descripcion, abre `Reusar concepto` y selecciona un concepto anterior
6. el sistema recalcula subtotal, impuesto y total
7. la venta queda disponible en listado, detalle y descarga documental
8. el PDF se renderiza en el momento de la descarga

**Flujos alternativos:**

- en edicion, el owner puede abrir `Reusar concepto`; la seleccion solo sustituye la descripcion, no la unidad
- si el numero de factura ya existe en la empresa, el sistema rechaza la operacion
- si el PDF falla por problema de entorno, la descarga devuelve error y la venta sigue existiendo

**Resultado esperado:**

- venta registrada y documento PDF disponible bajo demanda

### CU-010. Consultar estadisticas

**Actor principal:** Owner

**Objetivo:** revisar el estado operativo y economico del negocio.

**Precondiciones:**

- existen datos de recogidas y/o ventas

**Flujo principal:**

1. el owner accede al dashboard o a la pantalla de estadisticas
2. consulta indicadores agregados
3. revisa evolucion, balance e historico

**Resultado esperado:**

- el owner puede interpretar costes, ingresos y beneficio neto

### CU-010B. Gestionar configuracion global de empresa

**Actor principal:** Owner

**Objetivo:** mantener los parametros operativos y fiscales que afectan a recogidas y facturas.

**Precondiciones:**

- el owner esta autenticado
- existe una empresa asociada al owner

**Flujo principal:**

1. el owner accede al modulo de configuracion
2. actualiza precio global por litro, datos fiscales o hub
3. guarda cada bloque de forma independiente
4. el sistema valida y persiste la configuracion

**Resultado esperado:**

- la empresa conserva parametros globales reutilizables por nuevos flujos operativos y economicos

### CU-010C. Marcar una recogida como facturable o no facturable

**Actor principal:** Owner

**Objetivo:** decidir si una recogida confirmada debe participar en el bloque economico.

**Precondiciones:**

- existe una `Collection`
- el owner puede editar la recogida

**Flujo principal:**

1. el owner abre el detalle o la edicion de la recogida
2. revisa estado, medicion e importe
3. marca la recogida como facturable o no facturable
4. guarda la informacion

**Resultado esperado:**

- la recogida mantiene su valor operativo, pero su impacto economico queda controlado segun la decision tomada

## 4. Casos de uso del worker

### CU-011. Consultar rutas asignadas

**Actor principal:** Worker

**Objetivo:** conocer las rutas y jornadas que debe operar.

**Precondiciones:**

- el worker esta autenticado

**Flujo principal:**

1. el worker accede al modulo de rutas
2. visualiza sus rutas operativas y jornadas asociadas
3. accede al detalle o a la ejecucion

**Resultado esperado:**

- el worker conoce que ruta debe operar

### CU-012. Iniciar jornada operativa

**Actor principal:** Worker

**Objetivo:** comenzar la ejecucion real de una jornada.

**Precondiciones:**

- existe un `RouteDay` valido
- el worker tiene permisos sobre la jornada

**Flujo principal:**

1. el worker abre `RouteExecution`
2. selecciona el dia correspondiente
3. pulsa iniciar jornada
4. el sistema registra hora de inicio y actualiza estado

**Resultado esperado:**

- la jornada pasa a estado en curso

### CU-013. Registrar parada recogida

**Actor principal:** Worker

**Objetivo:** marcar la siguiente parada como atendida y crear o actualizar la recogida asociada.

**Precondiciones:**

- la jornada esta iniciada
- existe una parada pendiente

**Flujo principal:**

1. el worker selecciona la parada activa
2. abre el formulario de recogida
3. registra los datos operativos disponibles
4. confirma la accion
5. el sistema actualiza la parada y crea o actualiza `Collection`

**Resultado esperado:**

- la parada deja de estar pendiente

### CU-014. Cancelar una parada

**Actor principal:** Worker

**Objetivo:** reflejar que una parada no ha podido recogerse.

**Precondiciones:**

- la parada pertenece a la jornada operada

**Flujo principal:**

1. el worker marca la parada como cancelada
2. el sistema actualiza el estado de la parada
3. el sistema la considera procesada a efectos de cierre de jornada

**Resultado esperado:**

- la parada queda cancelada y no sigue apareciendo como pendiente

### CU-015. Finalizar jornada

**Actor principal:** Worker

**Objetivo:** cerrar la jornada una vez procesadas las paradas.

**Precondiciones:**

- existe una jornada iniciada

**Flujo principal:**

1. el worker pulsa finalizar jornada
2. el sistema revisa si quedan pendientes
3. si no quedan pendientes, la jornada se completa
4. si quedan pendientes, el sistema obliga a decidir entre cierre parcial o cancelacion

**Resultado esperado:**

- la jornada queda cerrada con un estado coherente

## 5. Casos de uso del client

### CU-016. Consultar solicitud de recogida

**Actor principal:** Client

**Objetivo:** conocer que solicitud tiene pendiente y para que fecha.

**Precondiciones:**

- existe una `CollectionRequest` asociada al cliente

**Flujo principal:**

1. el client accede a su area funcional
2. consulta la solicitud pendiente
3. revisa fecha y limite de respuesta

**Resultado esperado:**

- el client entiende que se le esta pidiendo una estimacion

### CU-017. Responder envases disponibles

**Actor principal:** Client

**Objetivo:** indicar cuantos bidones o IBC tiene disponibles antes de la recogida.

**Precondiciones:**

- la solicitud sigue dentro de plazo o en estado respondible

**Flujo principal:**

1. el client abre la solicitud
2. selecciona tipo de envase
3. introduce la cantidad de envases
4. confirma la respuesta
5. el sistema calcula litros equivalentes, actualiza el estado y registra autoria y momento de respuesta

**Flujos alternativos:**

- si la solicitud ya expiro, puede no permitir respuesta directa segun regla vigente

**Resultado esperado:**

- la solicitud queda respondida por el cliente

### CU-018. Consultar historico de recogidas

**Actor principal:** Client

**Objetivo:** revisar las recogidas pasadas asociadas a su cuenta.

**Precondiciones:**

- existen recogidas historicas para ese cliente

**Flujo principal:**

1. el client accede al modulo correspondiente
2. consulta listado e informacion resumida
3. revisa detalles si la interfaz lo permite

**Resultado esperado:**

- el client puede consultar su historico operativo

## 6. Casos de uso automaticos del sistema

### CU-019. Autoestimar una solicitud expirada

**Actor principal:** Sistema

**Objetivo:** evitar que una solicitud no respondida bloquee la operacion.

**Precondiciones:**

- existe una solicitud programada para expiracion
- el cliente no ha respondido a tiempo

**Flujo principal:**

1. Celery ejecuta la tarea programada
2. el sistema comprueba el estado actual de la solicitud
3. el sistema calcula o asigna el valor de autoestimacion
4. el sistema registra la resolucion automatica

**Resultado esperado:**

- la solicitud queda cerrada sin intervencion manual

### CU-020. Enviar notificacion de solicitud

**Actor principal:** Sistema

**Objetivo:** comunicar al cliente que tiene una estimacion pendiente.

**Precondiciones:**

- la integracion de correo esta configurada
- el cliente tiene email disponible

**Flujo principal:**

1. se crea la solicitud
2. se dispara la tarea de notificacion
3. el sistema renderiza la plantilla HTML comun
4. se envia el correo

**Flujos alternativos:**

- si Gmail API no esta disponible, la notificacion se omite y se deja logging

**Resultado esperado:**

- el cliente recibe un aviso o, en su defecto, la operacion continua sin bloqueo

### CU-021. Generar PDF de factura

**Actor principal:** Sistema

**Objetivo:** producir al instante el documento PDF asociado a una venta cuando el owner lo descarga.

**Precondiciones:**

- la venta es valida
- existen datos suficientes de emisor y comprador

**Flujo principal:**

1. el sistema construye el contexto documental
2. renderiza la plantilla HTML
3. genera el PDF con WeasyPrint
4. devuelve el binario al navegador sin almacenar el documento como fichero operativo persistente

**Resultado esperado:**

- el owner descarga una factura PDF construida con los datos vigentes de la venta, comprador y configuracion fiscal de empresa

### CU-022. Recalcular documento tras cambios de datos

**Actor principal:** Sistema

**Objetivo:** garantizar que la factura descargada refleja siempre la informacion actual.

**Precondiciones:**

- existe una venta registrada
- el owner ha modificado datos de venta, comprador o configuracion fiscal

**Flujo principal:**

1. el owner solicita de nuevo la descarga de factura
2. el backend consulta los datos actuales
3. WeasyPrint vuelve a renderizar el PDF con ese contexto
4. el sistema entrega el documento actualizado

**Resultado esperado:**

- no hace falta endpoint de regeneracion ni limpiar ficheros antiguos, porque la factura se reconstruye bajo demanda

## 7. Observaciones finales

Estos casos de uso no sustituyen a la documentacion de requisitos ni a la documentacion funcional, pero ayudan a explicar el comportamiento del sistema de una forma muy util para:

- defensa academica
- onboarding funcional
- validacion manual de flujos
- preparacion de anexos de memoria

Vistos en conjunto, los casos de uso muestran que GreenPath coordina varios tipos de complejidad: reglas de negocio, estados operativos, procesos asincronos, geolocalizacion, documentos PDF y permisos por rol. Esa combinacion es una parte importante del valor defendible del TFG.

Tambien conviene leer este documento junto con:

- `docs/FUNCIONAL.md`
- `docs/REQUISITOS.md`
- `docs/MANUAL_USUARIO.md`
- `docs/ROUTE_FLOW.md`

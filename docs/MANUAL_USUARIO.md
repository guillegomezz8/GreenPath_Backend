# Manual de Usuario GreenPath

Fecha de revision: 2026-03-31

## 1. Objetivo del documento

Este manual describe el uso del sistema GreenPath desde la perspectiva de sus usuarios. Su objetivo es servir como anexo funcional y como apoyo para una posible defensa o entrega del proyecto.

Se organiza por rol, porque la experiencia de uso cambia significativamente entre owner, worker y client.

## 2. Requisitos previos de uso

Antes de utilizar la aplicacion, deben cumplirse estas condiciones:

- disponer de un usuario valido en el sistema
- acceder a la URL del frontend
- contar con backend y servicios asociados operativos
- en modulos geograficos o documentales, disponer de los datos minimos necesarios para que el sistema pueda trabajar correctamente

## 3. Acceso a la plataforma

### 3.1 Inicio de sesion

El usuario accede mediante:

- email o username y contrasena
- login social, cuando la configuracion lo permite

Tras autenticarse, el sistema redirige al usuario a una experiencia adaptada a su rol.

### 3.2 Cierre de sesion

La aplicacion permite cerrar sesion desde la navegacion principal. Esta accion invalida la sesion activa en frontend y evita que otra persona reutilice la misma pantalla sin autenticacion.

## 4. Manual del owner

El owner es el usuario con mayor cobertura funcional dentro del sistema.

### 4.1 Modulos disponibles

El owner puede acceder, en general, a:

- dashboard
- clientes
- trabajadores
- camiones
- zonas de recogida
- rutas
- recogidas
- compradores
- ventas
- configuracion
- estadisticas

### 4.2 Gestion de clientes

Desde el modulo de clientes, el owner puede:

- listar clientes
- buscar y filtrar
- crear un cliente
- editar un cliente
- consultar su detalle e historico

Al crear un cliente, conviene introducir correctamente:

- direccion
- ciudad
- codigo postal
- pais

Esto facilita la geocodificacion automatica y su uso posterior en rutas.

### 4.3 Gestion de trabajadores

Desde el modulo de trabajadores, el owner puede:

- listar trabajadores
- crear trabajadores operativos
- editar informacion permitida
- consultar detalle e historico

Los usuarios owner o administradores avanzados se recomiendan crear desde Django Admin, no desde el flujo normal del frontend.

### 4.4 Gestion de camiones

Desde el modulo de camiones, el owner puede:

- crear y editar camiones
- asignar conductor
- consultar estado de la flota

### 4.5 Gestion de zonas

Desde el modulo de zonas, el owner puede:

- crear zonas geograficas de recogida
- editar poligonos
- consultar zonas existentes

Es recomendable que las zonas esten definidas con el mayor cuidado posible para evitar solapes innecesarios o clientes mal clasificados.

### 4.6 Gestion de rutas

Desde el modulo de rutas, el owner puede:

- crear una ruta plantilla
- editarla
- asignar trabajador
- definir zonas por dia
- consultar el detalle de planificacion
- generar una semana operativa

### 4.7 Generacion semanal

Para generar una semana:

1. acceder al detalle o al listado de rutas
2. abrir la accion `Generar semana`
3. seleccionar la semana deseada
4. introducir capacidad global o por fecha
5. confirmar la operacion

El sistema generara:

- jornadas (`RouteDay`)
- paradas (`RouteDayClient`)
- solicitudes de estimacion

### 4.8 Ejecucion de ruta

Aunque el worker es quien normalmente opera la jornada, el owner tambien puede usar la vista de ejecucion. Desde esa pantalla puede:

- seleccionar el dia operativo
- iniciar la jornada
- consultar el mapa
- abrir navegacion externa
- registrar paradas
- finalizar la jornada

### 4.9 Gestion de recogidas

Desde el modulo de recogidas, el owner puede:

- crear recogidas manuales
- consultar detalle
- editar una recogida
- medir litros reales
- aplicar deducciones
- marcar la recogida como facturable o no facturable

La casilla `Facturable` es importante porque decide si la recogida entra en estadisticas economicas.

### 4.10 Gestion de compradores

Desde el modulo de compradores, el owner puede:

- crear compradores internos
- mantener sus datos fiscales
- consultarlos y editarlos

Estos compradores no acceden a la plataforma; sirven como soporte para ventas y facturas.

### 4.11 Gestion de ventas

Desde el modulo de ventas, el owner puede:

- crear ventas
- consultar detalle
- editar ventas
- descargar factura PDF
- regenerar la factura si es necesario

Para crear una venta, debe indicar:

- comprador
- numero de factura
- fecha de factura
- descripcion
- cantidad
- unidad
- precio unitario
- IVA

### 4.12 Configuracion de empresa

Desde configuracion, el owner puede mantener:

- precio por litro
- hub de empresa
- datos fiscales
- datos bancarios
- codigo LER

La pantalla se organiza por bloques para que cada seccion pueda guardarse de forma independiente.

### 4.13 Estadisticas

El owner puede consultar:

- costes
- ingresos
- beneficio neto
- resumenes operativos
- evolucion temporal

La lectura correcta del sistema economico es:

- recogidas confirmadas y facturables = coste
- ventas = ingreso

## 5. Manual del worker

El worker esta orientado a la ejecucion operativa.

### 5.1 Modulos disponibles

Normalmente dispone de acceso a:

- dashboard
- rutas
- recogidas propias o relacionadas
- perfil de usuario

### 5.2 Consulta de rutas

Desde el modulo de rutas, el worker puede consultar:

- rutas asignadas
- detalle de la ruta
- jornadas disponibles

### 5.3 Ejecucion de jornada

El flujo habitual del worker es:

1. abrir la ruta
2. entrar en `Realizar ruta`
3. seleccionar la jornada
4. iniciar la jornada
5. registrar cada parada
6. finalizar la jornada

### 5.4 Registro de una parada

Cuando el worker registra una parada, puede:

- confirmar la recogida
- cancelar la parada

La medicion economica final puede quedar pendiente para revision posterior por owner.

### 5.5 Perfil

El worker puede revisar y actualizar la informacion personal permitida desde su perfil.

## 6. Manual del client

El client representa al cliente de recogida con acceso limitado al portal.

### 6.1 Modulos disponibles

El client dispone, principalmente, de:

- panel o dashboard limitado
- solicitudes de recogida
- historico de recogidas
- perfil

### 6.2 Responder una solicitud

Cuando el sistema crea una `CollectionRequest`, el client puede:

1. abrir la solicitud pendiente
2. revisar la fecha de recogida prevista
3. introducir la estimacion de litros
4. confirmar su respuesta

### 6.3 Revisar historico

El client puede consultar el historico de recogidas asociadas a su cuenta, incluyendo estados y datos basicos del servicio realizado.

## 7. Recomendaciones de uso

### 7.1 Para datos geograficos

- introducir direcciones lo mas completas posible
- revisar clientes sin coordenadas
- mantener zonas bien definidas

### 7.2 Para operacion diaria

- usar la pantalla de ejecucion de ruta en movil
- no mezclar detalle de ruta con operacion diaria
- registrar cancelaciones correctamente para no dejar pendientes falsos

### 7.3 Para bloque economico

- medir litros antes de considerar cerrada economicamente una recogida
- revisar la casilla `Facturable`
- mantener al dia la configuracion de empresa antes de emitir facturas

## 8. Problemas habituales y resolucion basica

| Situacion | Recomendacion |
| --- | --- |
| Un cliente no aparece en la semana generada | Revisar frecuencia, coordenadas, empresa y zonas del dia |
| Una ruta no se optimiza con Google | Revisar clave API o asumir fallback secuencial |
| Un correo no se envia | Revisar configuracion de Gmail API y logs |
| Una recogida no computa en estadisticas | Revisar estado y casilla `Facturable` |
| Una venta no genera PDF correctamente | Revisar datos fiscales y entorno de WeasyPrint |

## 9. Documentos relacionados

Este manual se complementa especialmente con:

- `docs/FRONTEND_PANTALLAS.md`
- `docs/FUNCIONAL.md`
- `docs/CASOS_DE_USO.md`
- `docs/API.md`

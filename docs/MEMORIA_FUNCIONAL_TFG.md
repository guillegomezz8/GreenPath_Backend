# Memoria Funcional TFG - GreenPath

Fecha de revision: 2026-03-24

## 1. Introduccion

GreenPath es una plataforma web orientada a la gestion integral de la recogida de aceite usado y a su explotacion economica posterior. El proyecto nace de una necesidad concreta de negocio: disponer de un sistema unificado para planificar rutas, ejecutar recogidas, mantener trazabilidad operativa y medir correctamente el impacto economico de la actividad.

En muchos escenarios reales, la gestion de este tipo de operacion se reparte entre hojas de calculo, mensajes, llamadas telefonicas, documentos manuales y conocimiento informal de las personas que operan la ruta. Esa fragmentacion impide responder con seguridad a preguntas tan basicas como:

- que clientes deben recogerse cada semana
- que se ha recogido realmente y que no
- cuanto cuesta la operacion
- cuanto se ha ingresado por ventas
- cual es el beneficio neto del periodo

GreenPath se plantea como una respuesta integral a ese problema. No se limita a almacenar informacion, sino que conecta planificacion, operacion, documentacion y analitica en una unica herramienta.

### 1.1 Contexto y motivacion

La motivacion principal del proyecto es doble.

Por una parte, existe una necesidad funcional real: transformar una operacion de recogida en un proceso digital, trazable y repetible. Por otra, desde el punto de vista academico, el proyecto permite trabajar con un dominio mas rico que el de una aplicacion CRUD tradicional, porque incorpora:

- geolocalizacion y datos espaciales
- permisos por rol y empresa
- planificacion con reglas de frecuencia
- procesos asincronos
- generacion documental en PDF
- integraciones externas
- medicion economica del negocio

### 1.2 Stakeholders principales

Los stakeholders mas relevantes del sistema son:

| Stakeholder | Interes principal | Papel en el sistema |
| --- | --- | --- |
| Owner | Control global del negocio | Configura, planifica, mide, vende y analiza |
| Worker | Operacion diaria | Ejecuta rutas y registra recogidas |
| Client | Colaboracion previa a la recogida | Responde solicitudes y consulta su historico |
| Buyer | Relacion comercial | Figura en ventas y facturas, sin acceso a plataforma |
| Tutor / evaluador academico | Validacion del proyecto | Stakeholder academico del TFG |

### 1.3 Estado del arte resumido

En este dominio suelen encontrarse tres tipos de aproximaciones:

- gestion manual con hojas de calculo
- software generico de gestion o ERP
- herramientas de reparto o de rutas no adaptadas al flujo real del negocio

La principal limitacion de esas alternativas es que resuelven solo una parte del problema. Algunas ayudan a registrar datos, otras a organizar recorridos y otras a facturar, pero no conectan de forma natural la configuracion geografica, la ejecucion diaria, la medicion posterior y el bloque economico de ventas.

GreenPath se diferencia por integrar en una misma solucion:

- rutas plantilla y generacion semanal
- soporte geoespacial con clientes y zonas
- solicitudes previas al cliente
- ejecucion diaria en movil
- recogidas con medicion posterior
- compradores, ventas y facturacion PDF
- estadisticas con coste, ingreso y beneficio

### 1.4 Objetivo general

Desarrollar una plataforma web multiusuario que permita a una empresa de recogida de aceite usado planificar rutas, ejecutar recogidas, registrar ventas, emitir facturas PDF y consultar indicadores economicos y operativos desde una unica solucion coherente.

### 1.5 Objetivos especificos

#### Objetivos tecnicos

- modularizar el sistema por dominios funcionales
- automatizar la generacion semanal de rutas operativas
- facilitar la ejecucion diaria de jornadas desde movil
- integrar soporte geoespacial real con PostGIS
- incorporar tareas asincronas con Celery
- generar facturas PDF desde plantillas HTML
- dotar al sistema de testing automatizado por modulos

#### Objetivos academicos

- aplicar conocimientos de ingenieria del software sobre un caso real
- trabajar con arquitectura full-stack y separacion por capas
- abordar decisiones de modelado de dominio y de permisos
- documentar el proyecto con un enfoque academico y profesional
- justificar tecnicamente la solucion implementada

### 1.6 Estructura documental adoptada

Tomando como referencia la organizacion habitual de una memoria de TFG, el proyecto se apoya en varios documentos complementarios en lugar de concentrarlo todo en un unico fichero:

- `docs/FUNCIONAL.md` cubre el analisis funcional y las reglas de negocio
- `docs/REQUISITOS.md` formaliza requisitos de negocio, informacion, funcionales y no funcionales
- `docs/ARQUITECTURA_TECNICA.md` cubre arquitectura, stack e integraciones
- `docs/API.md` cubre contratos y endpoints
- `docs/FRONTEND_PANTALLAS.md` cubre la interfaz y el flujo por pantallas
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md` cubre APIs usadas, configuracion y riesgos
- `docs/TESTING.md` cubre validacion automatizada y manual
- `docs/PLANIFICACION_Y_COSTES.md` cubre metodologia, estimaciones, planificacion y costes
- `docs/CASOS_DE_USO.md` describe secuencias funcionales por actor
- `docs/MANUAL_USUARIO.md` sirve como anexo de uso del sistema

Esta memoria actua como documento academico de sintesis y de enlace entre todas esas piezas.

## 2. Vision general del sistema

GreenPath cubre el ciclo funcional principal del negocio:

1. configuracion de empresa y datos maestros
2. planificacion geografica de rutas
3. generacion semanal de jornadas y paradas
4. solicitud previa de litros al cliente
5. ejecucion diaria de la ruta
6. medicion y cierre economico de recogidas
7. gestion de compradores internos
8. registro de ventas
9. generacion de facturas PDF
10. analitica de costes, ingresos y beneficio

Esta vision es importante porque demuestra que el proyecto no es un conjunto de modulos aislados, sino un flujo completo de negocio.

## 3. Alcance funcional actual

El alcance actual del sistema incluye:

- autenticacion por usuario y rol
- gestion de clientes, trabajadores, camiones y zonas
- configuracion de rutas plantilla y zonas por dia
- generacion semanal de `RouteDay` y `RouteDayClient`
- solicitudes de estimacion al cliente (`CollectionRequest`)
- autoestimacion asincrona con Celery
- ejecucion diaria de la ruta desde interfaz responsive
- recogidas con medicion posterior y control de `billable`
- compradores internos (`Buyer`)
- ventas (`Sale`)
- generacion y regeneracion de facturas PDF
- configuracion fiscal y operativa por empresa
- dashboard y estadisticas

El catalogo formal de requisitos del proyecto se desarrolla en `docs/REQUISITOS.md`, mientras que esta memoria mantiene una vision de sintesis mas academica.

## 4. Aportacion del proyecto

### 4.1 Aportacion operativa

GreenPath mejora la operacion diaria porque:

- reduce la improvisacion en la asignacion de clientes
- formaliza la semana operativa
- separa configuracion y ejecucion
- favorece el uso movil en ruta
- deja trazabilidad sobre lo planificado y lo realmente ejecutado

### 4.2 Aportacion economica

El sistema aporta valor economico porque:

- distingue entre coste y ingreso
- incorpora recogidas facturables y no facturables
- permite medir el cierre economico despues de la medicion en nave
- integra compradores, ventas y facturas
- calcula beneficio neto sobre datos mas coherentes

### 4.3 Aportacion academica

Desde la perspectiva del TFG, el proyecto aporta complejidad suficiente en varios frentes:

- modelado de dominio real
- datos geoespaciales
- automatizacion con tareas diferidas
- seguridad y permisos por rol
- generacion documental
- trabajo frontend y backend desacoplado
- testing automatizado y documentacion extensa

## 5. Flujo funcional resumido

El flujo principal del sistema puede resumirse asi:

1. se configuran empresa, trabajadores, clientes, camiones, zonas y rutas
2. el owner genera una semana operativa
3. el sistema crea jornadas, paradas y solicitudes de estimacion
4. el cliente responde o el sistema autoestima si expira el plazo
5. owner o worker ejecutan la ruta diaria
6. la recogida se consolida despues con medicion en nave
7. el owner registra ventas y genera facturas
8. el sistema calcula costes, ingresos y beneficio

Este flujo resume bien la idea central del proyecto: unir una operacion fisica con su reflejo documental y economico.

## 6. Arquitectura y stack tecnologico

El sistema se apoya en una arquitectura cliente-servidor con desacoplamiento claro entre frontend y backend.

### 6.1 Stack principal

- Python 3.11
- Django
- Django REST Framework
- PostgreSQL + PostGIS
- Celery + Redis
- React + Vite
- Tailwind CSS
- Leaflet / React Leaflet
- WeasyPrint
- Google Maps / Directions API
- Gmail API
- Docker Compose

### 6.2 Decisiones arquitectonicas relevantes

Durante el proyecto se han consolidado varias decisiones tecnicas y funcionales importantes:

- separacion por apps de dominio en backend
- separacion entre `RouteDetail` y `RouteExecution` en frontend
- uso de una sola fecha operativa en ventas: `invoice_date`
- numero de factura manual y unico por empresa
- precio por litro configurable a nivel de empresa
- bandera `facturable` en recogidas para impactar o no en estadisticas
- uso de Celery para no bloquear procesos operativos

La arquitectura detallada del sistema se desarrolla en `docs/ARQUITECTURA_TECNICA.md`.

### 6.3 APIs e integraciones utilizadas

GreenPath utiliza varias integraciones relevantes:

- Google Maps Platform para geocodificacion y optimizacion de rutas
- Gmail API para notificaciones y correos de acceso
- WeasyPrint para generacion de facturas PDF

La explicacion detallada de estas integraciones, su configuracion, su criticidad y su comportamiento ante fallos se recoge en `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`.

## 7. Estado actual de calidad y validacion

A fecha de esta revision, el sistema cubre el flujo principal del negocio y dispone de:

- backend funcional por modulos
- frontend operativo por rol
- documentacion unificada en la carpeta `docs`
- soporte para operacion diaria y bloque economico
- testing automatizado modular

### 7.1 Snapshot de testing actual

- backend: 25 tests automatizados
- frontend: 17 tests automatizados

El detalle de estrategia, estructura y comandos se encuentra en `docs/TESTING.md`.

## 8. Planificacion, estimaciones y costes

Una de las carencias habituales en proyectos tecnicamente correctos pero academicamente incompletos es no explicar bien como se organizo el trabajo, cuanto esfuerzo se estima y como se podria valorar el proyecto desde un punto de vista de coste. Para cubrir ese hueco, GreenPath incorpora ya un documento especifico:

- `docs/PLANIFICACION_Y_COSTES.md`

Ese documento desarrolla:

- metodologia de trabajo
- fases y entregables
- estimacion de esfuerzo
- cronograma orientativo
- valoracion economica del proyecto
- riesgos y desviaciones razonables

Esta separacion permite mantener la memoria academica limpia y, al mismo tiempo, cubrir uno de los apartados que mas se echa en falta en muchas entregas tecnicas.

## 9. Posibles lineas futuras

Como evolucion posterior al alcance actual, el proyecto podria crecer en:

- integracion contable externa
- optimizacion avanzada de rutas con mas restricciones
- exportaciones financieras y auditoria
- portal especifico para compradores
- analitica mas avanzada
- testing end-to-end mas profundo

## 10. Conclusion

GreenPath resuelve de manera integrada una necesidad real de negocio: transformar la gestion de recogida de aceite usado en un proceso digital, trazable y medible.

La plataforma no solo organiza la operacion diaria, sino que conecta esa operacion con el resultado economico del negocio, incorporando ventas, facturacion y estadisticas. Desde el punto de vista academico y profesional, esto convierte el proyecto en una solucion completa, con valor practico y con una arquitectura suficientemente rica como para sostener una memoria de TFG amplia y defendible.

## 11. Documentacion complementaria

El resto de documentos del proyecto sirven como anexos tecnicos y funcionales de esta memoria:

- `docs/FUNCIONAL.md`
- `docs/REQUISITOS.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/API.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
- `docs/TESTING.md`
- `docs/ROUTE_FLOW.md`
- `docs/CASOS_DE_USO.md`
- `docs/MANUAL_USUARIO.md`
- `docs/HISTORIAS_USUARIO.md`
- `docs/PLANIFICACION_Y_COSTES.md`

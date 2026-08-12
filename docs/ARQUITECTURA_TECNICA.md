# Arquitectura Tecnica del Proyecto

Fecha de revision: 2026-05-27

## 1. Objetivo de esta documentacion

Este documento describe la arquitectura tecnica de GreenPath a alto y medio nivel.
Su objetivo es facilitar:

- onboarding tecnico
- mantenimiento evolutivo
- localizacion de responsabilidades por modulo
- comprension del flujo entre frontend, API, base de datos y tareas asincronas

## 2. Principios de arquitectura

GreenPath se apoya en varios principios tecnicos:

- modularidad por dominio funcional
- aislamiento de datos por empresa
- logica de negocio concentrada en backend
- frontend orientado a experiencia por rol
- uso de integraciones externas como complemento, no como dependencia absoluta del flujo base
- configuracion editable para evitar valores criticos hardcodeados
- preferencia por trazabilidad funcional antes que automatismo opaco
- separacion explicita entre operacion diaria, cierre economico y documentacion de venta

## 3. Stack tecnico

### 3.1 Backend

- Django
- Django REST Framework
- Django Filter
- PostGIS
- Celery
- Redis
- WeasyPrint

### 3.2 Frontend

- React
- Vite
- HashRouter con rutas privadas por rol
- Tailwind CSS
- componentes UI reutilizables propios
- Leaflet / React Leaflet para vistas geograficas
- librerias de soporte para formularios, iconografia y componentes responsivos

### 3.3 Infraestructura local

- Docker Compose
- contenedores para backend, frontend, postgres, redis, celery, celery beat y flower

### 3.4 Complejidad tecnica derivada del stack

La arquitectura no solo resuelve persistencia y vistas. Tambien debe coordinar:

- datos relacionales y geoespaciales
- procesos sincronos y asincronos
- integraciones con terceros
- generacion documental en PDF
- aislamiento multiempresa
- experiencia operativa responsive para uso en movilidad

Esta combinacion es una de las razones por las que GreenPath tiene entidad suficiente como proyecto de TFG amplio y no como ejercicio reducido de gestion administrativa.

## 4. Organizacion del backend

El backend se estructura por dominios en `apps/`.

### 4.1 `apps/base`

Responsabilidades:

- enums
- literals
- permisos
- logger
- utilidades comunes

### 4.2 `apps/user`

Responsabilidades:

- modelo `User`
- perfiles de `Client` y `Worker`
- serializers y viewsets de usuarios, clientes y trabajadores
- actualizacion de perfil propio, incluyendo imagen de perfil cuando aplica
- geocodificacion de clientes
- adaptacion del comportamiento por rol y empresa

### 4.3 `apps/company`

Responsabilidades:

- `Company`
- `CompanyHub`
- `CompanySettings`
- configuracion operativa y fiscal global

### 4.4 `apps/zone`

Responsabilidades:

- gestion de zonas geograficas de recogida
- almacenamiento de poligonos

### 4.5 `apps/truck`

Responsabilidades:

- gestion de flota
- asignacion de conductor a camion

### 4.6 `apps/route`

Responsabilidades:

- `Route`
- `RouteZoneDay`
- `RouteDay`
- `RouteDayClient`
- generacion semanal
- ejecucion diaria
- calculo de tramos operativos por capacidad
- integracion con Google Directions
- construccion de navegacion externa alineada con el plan operativo

### 4.7 `apps/collection`

Responsabilidades:

- `CollectionRequest`
- `Collection`
- tareas Celery asociadas a expiraciones y notificaciones
- respuestas del cliente y resolucion manual

### 4.8 `apps/sale`

Responsabilidades:

- `Buyer`
- `Sale`
- generacion de facturas PDF
- resumen economico
- uso bajo demanda del documento de factura sin persistencia binaria

## 5. Modelado tecnico esencial

### 5.1 Jerarquia principal de operacion

- `Company`
- `Worker` / `Client`
- `Route`
- `RouteDay`
- `RouteDayClient`
- `CollectionRequest`
- `Collection`

### 5.2 Jerarquia principal de negocio economico

- `CompanySettings`
- `Buyer`
- `Sale`
- factura PDF renderizada bajo demanda

## 6. Flujo tecnico de generacion semanal

La accion `POST /routes/{route_id}/generate-week/` hace, a grandes rasgos, lo siguiente:

1. valida permisos
2. valida payload de entrada
3. resuelve la ventana semanal
4. crea o reutiliza `RouteDay`
5. obtiene las zonas del dia desde `RouteZoneDay`
6. selecciona clientes geograficamente dentro de las zonas
7. filtra por frecuencia y planificacion previa de la misma empresa
8. aplica limite de capacidad y maximo de clientes
9. crea o actualiza `RouteDayClient`
10. optimiza orden con Google si procede
11. crea o actualiza `CollectionRequest`
12. agenda tarea de autoestimacion

Este flujo concentra una parte importante de la complejidad del sistema porque mezcla reglas de negocio, geografia, frecuencia, capacidad, proteccion de dias ya operados y automatizaciones asincronas.

## 7. Flujo tecnico de ejecucion diaria

La ejecucion diaria esta separada de la planificacion.
El backend ofrece acciones especificas para:

- iniciar jornada
- registrar una parada
- finalizar jornada
- obtener enlace de navegacion

Esto permite que el frontend tenga una pantalla operativa (`RouteExecution`) distinta del detalle de ruta (`RouteDetail`).

### 7.1 `v1` de control por capacidad

La version actual incorpora una capa tecnica intermedia entre planificacion y navegacion:

- `build_route_day_operational_plan(route_day, ordered_clients=None)`

Esta funcion:

- resuelve la carga prevista de cada parada
- divide la jornada en segmentos si se supera `daily_capacity_liters`
- calcula tramo activo, carga registrada y capacidad restante
- devuelve un bloque `operational_plan` reutilizable por API, frontend y exportacion de navegacion

En el estado actual del producto, esa informacion se usa sobre todo como motor interno de decision:

- sugerir la siguiente parada adecuada
- construir el mapa operativo
- insertar retornos al hub en la navegacion exportada

La interfaz ya no necesita mostrar al usuario tarjetas tecnicas de `tramo` para aprovechar este calculo.

### 7.2 Ventaja tecnica del enfoque actual

La decision de no crear todavia tablas adicionales para viajes o descargas ofrece varias ventajas:

- no rompe el modelo actual de `RouteDay`
- evita migraciones y complejidad adicional en la `v1`
- mantiene un unico criterio de segmentacion para backend y frontend
- permite evolucion futura a una `v2` con persistencia real de tramos si el negocio la necesita

## 8. Flujo tecnico de solicitudes al cliente

### 8.1 Creacion

- se crea desde la generacion semanal
- se guarda `expires_at`
- se programa `auto_estimate_collection_request_liters`
- puede lanzarse correo de notificacion

### 8.2 Resolucion

La solicitud puede resolverse por tres vias:

- cliente responde a tiempo
- owner/worker intervienen manualmente
- Celery autoestima cuando expira

### 8.3 Trazabilidad

`CollectionRequest` guarda informacion de autoria y scheduling, por ejemplo:

- `answered_by`, `answered_at`
- `manual_by`, `manual_at`
- `auto_estimate_task_id`
- `auto_estimate_scheduled_at`

## 9. Flujo tecnico de recogidas

Una `Collection` puede nacer por dos caminos:

- alta manual desde el modulo de recogidas
- creacion/actualizacion al completar una parada de ruta

Elementos clave:

- `price_per_liter` puede venir por defecto de `CompanySettings`
- `billable` decide si la recogida participa en estadisticas economicas
- los importes agregados de cliente, trabajador y resumen economico filtran por `CONFIRMED` y `billable=true`

## 10. Flujo tecnico de ventas y facturacion

1. el owner crea una `Sale`
2. el frontend muestra como referencia el numero de la ultima factura y permite reusar conceptos anteriores sin modificar la unidad
3. el backend valida `invoice_number` y `invoice_date`
4. crea o reutiliza un `SaleInvoiceIssuerSnapshot` con los datos fiscales y bancarios actuales de la empresa
5. recalcula `subtotal`, `tax_amount` y `total`
6. sincroniza `sale_date` con `invoice_date`
7. renderiza el PDF con WeasyPrint solo cuando se solicita
8. expone descarga via endpoint dedicado sin persistir el fichero

Esta decision de generar el documento bajo demanda tiene dos ventajas arquitectonicas:

- evita persistencia innecesaria de binarios
- conserva los datos fiscales y bancarios historicos del emisor aunque cambie la configuracion global de empresa

## 11. Frontend y organizacion de pantallas

El frontend esta organizado por dominio funcional:

- `clients`
- `workers`
- `trucks`
- `collectionZones`
- `routes`
- `collections`
- `buyers`
- `sales`
- `settings`
- `stats`

Patrones destacables:

- layout comun con sidebar y topbar
- navegacion condicionada por rol
- pantallas de detalle separadas de pantallas de operacion cuando el caso lo exige
- componentes comunes para botones, filtros, contadores y estados vacios

### 11.1 Ejecucion de rutas

La pantalla `RouteExecution` y el componente `RouteDayMap` consumen el `operational_plan` para:

- seleccionar por defecto la siguiente parada pendiente adecuada
- mostrar el contexto operativo imprescindible sin sobrecargar la interfaz
- representar visualmente retornos al hub en el mapa
- mantener alineadas la experiencia visual y la URL de navegacion externa

## 12. Seguridad y permisos

La seguridad combina:

- autenticacion JWT
- restricciones por rol
- restricciones por empresa
- permisos dedicados para acciones sensibles

Ejemplos:

- `generate-week` solo owner
- compradores y ventas solo owner
- client solo ve sus solicitudes y recogidas
- worker solo opera rutas de su empresa y, normalmente, las que tiene asignadas
- configuracion fiscal y economica aislada por empresa
- el login correcto actualiza `last_login` y el fallo de credenciales no lo modifica

## 13. Integraciones externas

### 13.1 Google Maps / Directions

Uso actual:

- geocodificacion de clientes
- optimizacion del orden de paradas
- construccion de enlace de navegacion

Comportamiento esperado:

- si falta API key, el flujo principal no debe romperse
- el backend deja logs claros cuando la optimizacion no se aplica

### 13.2 Gmail API

Uso actual:

- alta de usuario con envio de acceso
- notificaciones de `CollectionRequest`

Comportamiento esperado:

- si no esta configurada, se omite la notificacion operativa sin tumbar el resto del flujo

### 13.2.1 Google Identity Services

Uso actual:

- login social en `src/pages/oauth/SocialLogin.jsx`
- validacion backend del Google ID token en `POST /authenticate/login`
- emision posterior de JWT propio de GreenPath

El frontend envia el token principalmente en el campo `token`; el backend mantiene compatibilidad aceptando tambien `credential`.

### 13.3 WeasyPrint

Uso actual:

- generacion de factura PDF desde HTML/CSS
- descarga documental bajo demanda

Consideraciones:

- requiere dependencias del sistema dentro de Docker
- anade complejidad de maquetacion, formato monetario y consistencia visual

### 13.4 Celery y Redis

Uso actual:

- autoestimacion de solicitudes expiradas
- notificaciones asincronas
- soporte de tareas programadas y diferidas

Valor tecnico:

- desacopla operaciones lentas del flujo HTTP
- mejora la experiencia de usuario
- permite una arquitectura mas realista y mas defendible academicamente

## 14. Observabilidad

El proyecto utiliza logging normalizado con formato por archivo y funcion.
Se busca que los logs permitan seguir:

- generacion semanal
- optimizacion Google
- tareas Celery
- envio de emails
- errores de validacion o integracion

## 15. Despliegue y dependencias del entorno

Para que el sistema funcione completo se necesitan:

- PostGIS para campos geograficos
- Redis para broker/result backend de Celery
- dependencias del sistema para WeasyPrint en la imagen Docker
- claves validas de Google y Gmail si se quieren usar integraciones externas

## 16. Riesgos tecnicos conocidos

- concurrencia extrema en regeneraciones semanales
- calidad irregular de datos geograficos
- dependencia de credenciales externas
- peso del bundle frontend, mejorable con code splitting

## 17. Recomendaciones de evolucion

- tests E2E del flujo de rutas
- tests del flujo de ventas y facturas
- monitorizacion especifica de tareas Celery
- endurecimiento de locks distribuidos si se despliega en multi-instancia

## 18. Ciclo de vida tecnico de una peticion

De forma simplificada, una peticion tipica en GreenPath sigue este recorrido:

1. el frontend autentica con JWT y llama a un endpoint DRF
2. el `ViewSet` resuelve permisos, queryset y serializer de entrada
3. el serializer valida estructura, tipos y reglas basicas
4. la logica de negocio se ejecuta en utilidades o metodos de dominio
5. el ORM persiste cambios en PostgreSQL/PostGIS
6. si aplica, se registran tareas asincronas en Celery
7. el serializer de salida devuelve datos enriquecidos para frontend
8. el frontend transforma la respuesta en estado de interfaz, tarjetas, tablas o mapas

Este patron se repite en la mayor parte del producto y explica por que el backend concentra la verdad funcional.

## 19. Mapa de tareas asincronas

Las tareas Celery cumplen un papel clave en dos zonas:

### 19.1 Solicitudes de recogida

- programacion de autoestimacion al expirar una `CollectionRequest`
- notificacion por email al cliente cuando se crea la solicitud
- revocacion y reprogramacion cuando cambia la planificacion

### 19.2 Correos y procesos diferidos

- envio de accesos a nuevos usuarios
- envio de notificaciones operativas
- desacoplamiento de acciones lentas para no bloquear la API principal

### 19.3 Consideraciones de arquitectura

- Redis actua como broker y backend de resultados
- Celery Beat permite programacion periodica cuando procede
- la persistencia de ids de tarea ayuda a evitar duplicidades basicas
- si el proyecto escala a multi-instancia, conviene endurecer locks distribuidos y deduplicacion

## 20. Persistencia geoespacial y documental

### 20.1 Persistencia geoespacial

GreenPath depende de PostGIS para:

- almacenar poligonos de zonas
- almacenar puntos de clientes y hub
- resolver inclusion geografica en zonas de ruta

Esto hace que la calidad de coordenadas no sea un detalle accesorio, sino una condicion estructural del flujo de planificacion.

### 20.2 Generacion documental

El sistema genera documentos de negocio en forma de PDF:

- facturas de venta ligadas a `Sale`
- posible documentacion complementaria asociada a medios o email

La generacion se hace con WeasyPrint a partir de plantillas HTML/CSS, lo que permite versionar la presentacion en el propio repositorio y reconstruir el documento en cada descarga con la venta, sus lineas y el snapshot fiscal asociado.

## 21. Validacion automatizada actual

GreenPath ya cuenta con una capa base de validacion automatizada tanto en backend como en frontend.

### 21.1 Backend

La estrategia backend combina:

- tests modulares por app
- helpers compartidos de test para contexto de empresa y usuarios
- validacion de permisos, API y reglas de negocio

Cobertura actual especialmente relevante:

- autenticacion y login
- permisos base y owner-only
- settings de empresa y hub
- CRUD critico de trabajadores, clientes, camiones y zonas
- `CollectionRequest`, `Collection` y filtro `billable`
- `generate-week` y cierre de `RouteDay`
- compradores, ventas y resumen economico

### 21.2 Frontend

La estrategia frontend usa:

- `Vitest`
- `@testing-library/react`
- `@testing-library/user-event`
- mocks de API y contexto para aislar pantallas por modulo

Cobertura actual especialmente relevante:

- `WorkerCreate` y `WorkerEdit`
- `BuyersList`
- `SaleForm` y `SaleDetail`
- `CollectionDetail`
- `ClientDetail`
- `GenerateWeekDialog`
- `CompanySettingsPage`
- `Stats`
- `TrucksList`
- `ProfilePage`

### 21.3 Alcance y limite actual

La cobertura actual protege reglas importantes de negocio y UX, pero todavia no sustituye:

- tests E2E completos de flujos largos
- tests de componentes mapa-heavy como `collectionZones`
- pruebas multi-dispositivo reales en rutas operativas

Por eso la estrategia recomendada sigue siendo mixta:

- tests automaticos para regresiones frecuentes
- validacion manual guiada para flujos GIS, PDF e integraciones externas

## 22. Topologia logica de servicios

En terminos de despliegue, GreenPath se organiza en varios servicios cooperativos:

- frontend para la interfaz web
- backend para API y reglas de negocio
- PostgreSQL/PostGIS para persistencia
- Redis para mensajeria y tareas
- Celery Worker para ejecucion asincrona
- Celery Beat para programacion
- Flower para observabilidad de colas

Esta separacion permite desacoplar responsabilidades y explicar con claridad que piezas son imprescindibles para la operacion base y cuales actuan como soporte.

## 23. Gobierno del dato y consistencia

La arquitectura persigue consistencia funcional en varios puntos:

- aislamiento de datos por empresa
- recalculo backend de importes sensibles
- preservacion de trazabilidad al regenerar semanas
- proteccion de jornadas ya operadas
- distincion entre dato operativo y dato economico

Ejemplos claros de esta filosofia:

- `Sale` recalcula subtotal, IVA y total en backend
- `Collection` separa estado operativo y marca `billable`
- `generate-week` protege dias ya ejecutados
- `CollectionRequest` mantiene autoria y scheduling

## 24. Relacion con despliegue y operacion

La arquitectura tecnica no termina en el codigo.
Su explotacion real depende de:

- variables de entorno correctas
- dependencias del sistema para WeasyPrint
- credenciales validas de Google y Gmail cuando se usan
- arranque coordinado de servicios Docker
- carga consistente de fixtures de demo cuando procede

La parte operativa detallada se desarrolla en:

- `docs/DESPLIEGUE_Y_OPERACION.md`

## 25. Relacion con la documentacion academica

Para una defensa o entrega del TFG, esta arquitectura se complementa con:

- `docs/FUNCIONAL.md` para la vision de negocio
- `docs/REQUISITOS.md` para la formalizacion de necesidades
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md` para justificar dependencias externas
- `docs/PLANIFICACION_Y_COSTES.md` para la dimension metodologica
- `docs/UML_BD.md` para explicar el modelo de datos


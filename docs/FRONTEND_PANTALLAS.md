# Guia de Pantallas Frontend GreenPath

Fecha de revision: 2026-04-30

## 1. Objetivo del documento

Este documento centraliza la documentacion funcional del frontend de GreenPath.
Su proposito es describir:

- que pantallas existen
- a que rol sirve cada una
- que acciones permite cada vista
- que endpoints consume de forma principal
- que consideraciones responsive y de UX son relevantes

La version actual recoge tambien el valor de las integraciones que llegan a la interfaz: mapas con Leaflet, navegacion externa de Google, facturas PDF bajo demanda, estados derivados de tareas Celery y datos economicos calculados desde backend.

Este documento sustituye a la documentacion funcional dispersa del frontend y se toma como referencia principal junto con:

- `docs/FUNCIONAL.md`
- `docs/API.md`
- `docs/ROUTE_FLOW.md`

## 2. Principios de la interfaz

El frontend actual sigue varios principios de producto:

- navegacion diferente por rol (`owner`, `worker`, `client`)
- separacion entre pantallas de consulta y pantallas de operacion
- prioridad a legibilidad y accion rapida en movil para rutas y recogidas
- reuse de componentes de filtros, contadores, modales y layouts
- integracion fuerte con backend, evitando datos hardcodeados siempre que el modulo ya este soportado por API

## 3. Navegacion por rol

### 3.1 Owner

Menu principal esperado:

- dashboard
- clientes
- trabajadores
- camiones
- zonas de recogida
- rutas
- recogidas
- compradores
- ventas
- estadisticas
- configuracion
- perfil

### 3.2 Worker

Menu principal esperado:

- rutas
- recogidas
- perfil

### 3.3 Client

Menu principal esperado:

- mis solicitudes
- mis recogidas
- perfil

## 4. Layout transversal

## 4.1 Sidebar

Archivo principal:

- `src/components/layout/Sidebar.jsx`

Responsabilidad:

- mostrar la navegacion por rol
- actuar como entrada al perfil desde foto/email
- ocultar modulos no autorizados

## 4.2 Topbar

Archivo principal:

- `src/components/layout/Topbar.jsx`

Responsabilidad:

- mostrar identidad de la sesion actual
- permitir cierre de sesion

## 4.3 MainLayout

Archivo principal:

- `src/components/layout/MainLayout.jsx`

Responsabilidad:

- envolver las pantallas privadas
- coordinar sidebar, topbar y contenido principal
- mantener un comportamiento estable entre movil y escritorio

## 5. Pantallas transversales

## 5.1 Login usuario/password

- Ruta: `/login`
- Archivo: `src/pages/oauth/Login.jsx`
- Estado: implementada
- Objetivo: autenticar con JWT
- Salida esperada: redireccion por rol al area correspondiente

## 5.2 Social login

- Ruta: `/socialLogin`
- Archivo: `src/pages/oauth/SocialLogin.jsx`
- Estado: implementada
- Objetivo: autenticar mediante Google
- Salida esperada: `owner -> /dashboard`, `worker -> /routes`, `client -> /my-requests`

## 5.3 Perfil de usuario

- Rutas: `/profile`, `/perfil`
- Archivo: `src/pages/profile/ProfilePage.jsx`
- Estado: implementada
- Funcionalidad:
  - ver datos del usuario
  - editar datos personales
  - cambiar contrasena
  - cambiar foto cuando aplique

## 5.4 Error 404

- Ruta: `*`
- Archivo: `src/pages/error/Error404.jsx`
- Estado: implementada

## 6. Dashboard

- Ruta: `/dashboard`
- Archivo: `src/pages/dashboard/Dashboard.jsx`
- Estado: implementada
- Acceso actual: `owner`

### Objetivo

Ser la puerta de entrada ejecutiva del owner.

### Variantes funcionales

- owner: KPIs operativos globales, actividad reciente y accesos rapidos
- worker: entrada directa por `/routes`
- client: entrada directa por `/my-requests`

### Notas de UX

- los contadores se pliegan en movil
- la actividad reciente prioriza estados operativos claros
- owner dispone de accesos rapidos a rutas operativas
- las badges largas de estado se adaptan a multilinea en movil para evitar recortes

## 7. Modulo de clientes

### 7.1 Listado de clientes

- Ruta: `/clients`
- Archivo: `src/pages/clients/ClientsList.jsx`
- Estado: implementada

Objetivo:

- consultar cartera de clientes
- filtrar por datos relevantes
- acceder rapidamente a detalle, edicion o alta de recogida

Notas:

- listado alineado con filtros reales de backend
- contadores resumidos y experiencia responsive

### 7.2 Alta de cliente

- Ruta: `/clients/new`
- Archivo: `src/pages/clients/ClientCreate.jsx`
- Estado: implementada

Objetivo:

- crear cliente con datos validos desde el primer intento

Notas:

- campos obligatorios alineados con backend
- direccion estructurada para permitir geocodificacion

### 7.3 Detalle de cliente

- Ruta: `/clients/:id`
- Archivo: `src/pages/clients/ClientDetail.jsx`
- Estado: implementada

Objetivo:

- ver ficha completa del cliente
- consultar su historial paginado de recogidas
- revisar su impacto economico facturable

Notas:

- el historial indica estado y condicion facturable/no facturable
- el total economico mostrado usa solo recogidas confirmadas y facturables

### 7.4 Edicion de cliente

- Ruta: `/clients/:id/edit`
- Archivo: `src/pages/clients/ClientEdit.jsx`
- Estado: implementada

## 8. Modulo de trabajadores

### 8.1 Listado de trabajadores

- Ruta: `/workers`
- Archivo: `src/pages/workers/WorkersList.jsx`
- Estado: implementada

Objetivo:

- consultar equipo operativo
- activar o desactivar trabajadores
- revisar camion asignado y acceso al detalle

### 8.2 Alta de trabajador

- Ruta: `/workers/new`
- Archivo: `src/pages/workers/WorkerCreate.jsx`
- Estado: implementada

Notas:

- el formulario crea solo trabajadores operativos normales
- no expone seleccion de rol ni de empresa
- la creacion de owners o administradores avanzados queda fuera del flujo normal del frontend

### 8.3 Detalle de trabajador

- Ruta: `/workers/:id`
- Archivo: `src/pages/workers/WorkerDetail.jsx`
- Estado: implementada

Objetivo:

- ver ficha completa del trabajador
- consultar su historial de recogidas
- revisar ingresos facturables asociados

Notas:

- el bloque economico usa solo recogidas confirmadas y facturables
- los botones de accion siguen el mismo patron visual que en clientes

### 8.4 Edicion de trabajador

- Ruta: `/workers/:id/edit`
- Archivo: `src/pages/workers/WorkerEdit.jsx`
- Estado: implementada

Notas:

- la edicion no permite cambiar el rol
- si el registro corresponde a un owner, la pantalla lo refleja como `Propietario` sin degradarlo a `worker`
- el backend ignora o bloquea cambios de `role` y `company` por este flujo

## 9. Modulo de camiones

### Pantallas

- `/trucks`
- `/trucks/new`
- `/trucks/:id/edit`
- `/assign-truck/:id`

Archivos:

- `src/pages/trucks/TrucksList.jsx`
- `src/pages/trucks/TruckCreate.jsx`
- `src/pages/trucks/TruckEdit.jsx`
- `src/pages/trucks/AssignTruck.jsx`

Estado:

- implementadas

Objetivo:

- gestionar la flota y asignar conductor cuando proceda

## 10. Modulo de zonas

### Pantalla principal

- Ruta: `/collection-zones`
- Archivo: `src/pages/collectionZones/CollectionZonesList.jsx`
- Estado: implementada

Objetivo:

- crear, editar y borrar zonas geograficas
- dibujar poligonos sobre mapa

## 11. Modulo de rutas

El frontend de rutas esta dividido en varias experiencias.

### 11.1 Listado de rutas

- Ruta: `/routes`
- Archivo: `src/pages/routes/RoutesList.jsx`
- Estado: implementada

Objetivo:

- listar rutas plantilla
- filtrar por asignacion de trabajador
- abrir detalle o entrar en ejecucion
- lanzar generacion semanal

Notas:

- acciones jerarquizadas visualmente
- contadores plegables en movil
- modal de generacion compartido

### 11.2 Creacion de ruta

- Ruta: `/routes/new`
- Archivos:
  - `src/pages/routes/RouteCreate.jsx`
  - `src/pages/routes/RouteForm.jsx`
- Estado: implementada

### 11.3 Detalle de ruta

- Ruta: `/routes/:id`
- Archivo: `src/pages/routes/RouteDetail.jsx`
- Estado: implementada

Objetivo:

- pantalla de planificacion semanal
- consultar `RouteDay`, estados, paradas y capacidades
- lanzar o revisar generacion de semana

Notas:

- no concentra la operacion diaria completa
- se reserva para consulta y supervision

### 11.4 Edicion de ruta

- Ruta: `/routes/:id/edit`
- Archivos:
  - `src/pages/routes/RouteEdit.jsx`
  - `src/pages/routes/RouteForm.jsx`
- Estado: implementada

### 11.5 Ejecucion de ruta

- Ruta: `/routes/:id/execute`
- Archivo: `src/pages/routes/RouteExecution.jsx`
- Estado: implementada

Objetivo:

- ejecutar la jornada diaria
- usar mapa, parada activa y acciones operativas desde una sola vista

Notas clave:

- pensada con foco en movil
- separada del detalle para reducir sobrecarga visual
- integra modales de registrar recogida y finalizar jornada
- fija por defecto la semana operativa actual
- consume `operational_plan` de forma interna para sugerir la siguiente parada y construir la navegacion
- el mapa dibuja retornos al hub cuando la jornada exige varias cargas, sin exponer tarjetas tecnicas de `tramo`

### 11.6 Componentes relevantes del modulo

- `src/components/routes/GenerateWeekDialog.jsx`
- `src/components/routes/RouteDayMap.jsx`
- `src/components/routes/RouteActionButton.jsx`

## 12. Modulo de recogidas

### 12.1 Listado de recogidas

- Ruta: `/collections`
- Archivo: `src/pages/collections/CollectionsList.jsx`
- Estado: implementada

Objetivo:

- consultar recogidas por estado
- acceder a detalle y edicion
- lanzar alta manual cuando el rol lo permite

Notas:

- contadores plegables en movil
- resumen de pagina con litros e importe
- la UI de `Facturable` se ha simplificado para evitar ruido visual

### 12.2 Alta de recogida

- Ruta: `/collections/new`
- Archivo: `src/pages/collections/CollectionCreate.jsx`
- Estado: implementada

Objetivo:

- registrar una recogida manual

Notas:

- `price_per_liter` se precarga desde configuracion global
- `Facturable` se maneja con una marca simple

### 12.3 Detalle de recogida

- Ruta: `/collections/:id`
- Archivo: `src/pages/collections/CollectionDetail.jsx`
- Estado: implementada

Objetivo:

- revisar detalle operativo y economico de la recogida

Notas:

- se muestra el motivo de deduccion traducido
- la condicion `Facturable` se muestra sin duplicidades

### 12.4 Edicion de recogida

- Ruta: `/collections/:id/edit`
- Archivo: `src/pages/collections/CollectionEdit.jsx`
- Estado: implementada

Objetivo:

- completar medicion en nave y ajustar datos economicos

Notas:

- flujo enfocado a `PENDING_MEASUREMENT`
- la marca `Facturable` se edita de forma directa

## 13. Modulo de solicitudes del cliente

### Pantalla principal

- Ruta: `/my-requests`
- Archivo: `src/pages/collections/CollectionRequestsPage.jsx`
- Estado: implementada

Objetivo:

- listar solicitudes pendientes o resueltas del cliente
- mostrar todos los estados por defecto y filtrar por estado desde un dropdown
- ordenar por creacion descendente, dejando primero las solicitudes mas nuevas
- responder dentro del plazo indicando tipo de envase (`BIDONES` o `IBC`) y cantidad
- calcular visualmente los litros derivados del numero de envases antes de enviar

Notas:

- la respuesta recomendada usa `container_type` y `container_number`
- el backend calcula `final_liters` y sincroniza `estimated_liters` para que no prevalezca visualmente la autoestimacion
- `final_liters` queda como compatibilidad legacy, no como flujo principal de cliente

## 14. Modulo de compradores

### Pantallas

- `/buyers`
- `/buyers/new`
- `/buyers/:id`
- `/buyers/:id/edit`

Archivos:

- `src/pages/buyers/BuyersList.jsx`
- `src/pages/buyers/BuyerCreate.jsx`
- `src/pages/buyers/BuyerDetail.jsx`
- `src/pages/buyers/BuyerEdit.jsx`
- `src/pages/buyers/BuyerForm.jsx`

Estado:

- implementadas

Objetivo:

- mantener la cartera interna de compradores con sus datos fiscales

Notas:

- modulo solo visible para owner
- filtros por ciudad, provincia y datos de contacto
- estado vacio y comportamiento responsive revisados

## 15. Modulo de ventas

### Pantallas

- `/sales`
- `/sales/new`
- `/sales/:id`
- `/sales/:id/edit`

Archivos:

- `src/pages/sales/SalesList.jsx`
- `src/pages/sales/SaleCreate.jsx`
- `src/pages/sales/SaleDetail.jsx`
- `src/pages/sales/SaleEdit.jsx`
- `src/pages/sales/SaleForm.jsx`

Estado:

- implementadas

Objetivo:

- registrar operaciones de venta y gestionar su factura PDF

Notas:

- solo visible para owner
- `invoice_number` manual
- en alta, el placeholder de `invoice_number` muestra el numero de la ultima factura como referencia
- `invoice_date` como fecha funcional unica
- la unidad por defecto del formulario es `kg`
- el formulario de alta y edicion permite reusar conceptos de facturas anteriores mediante modal
- el modal `Reusar concepto` copia solo la descripcion, no modifica la unidad seleccionada
- si hay 5 o mas conceptos reutilizables, el modal usa scroll interno para mantener comportamiento responsive
- detalle con descarga directa de factura bajo demanda

## 16. Modulo de configuracion de empresa

### Pantalla principal

- Ruta: `/settings`
- Archivo: `src/pages/settings/CompanySettingsPage.jsx`
- Estado: implementada

Objetivo:

- centralizar ajustes operativos y fiscales

Bloques principales:

- precio global por litro
- datos de facturacion
- hub de empresa

Notas:

- cada bloque funciona como dropdown independiente
- cada bloque tiene guardar/restablecer propios
- el hub se selecciona sobre mapa
- el logo de facturacion ya no forma parte del flujo funcional

## 17. Modulo de estadisticas

### Pantalla principal

- Ruta: `/stats`
- Archivo: `src/pages/stats/Stats.jsx`
- Estado: implementada

Objetivo:

- ofrecer vision economica y operativa sintetica al owner

Contenido actual:

- costes por recogidas confirmadas y facturables
- ingresos por ventas
- beneficio neto
- volumen comprado vs vendido
- filtro por rango de fechas usando `start_date` y `end_date` sobre `GET /sales/economic-summary/`
- leyenda visual de colores por grafica
- scroll horizontal controlado en charts estrechos

## 18. Responsive y criterios de UX

El frontend sigue varias decisiones practicas para mantener usabilidad en movil:

- contadores plegables en listados y dashboard
- filtros apilables o en grid en pantallas pequenas
- modales con scroll interno y CTA apiladas
- separacion entre detalle y operativa en el modulo de rutas
- tarjetas en lugar de tablas cuando la tabla penaliza demasiado la experiencia movil

Zonas donde la responsividad es especialmente critica:

- `RouteExecution`
- `GenerateWeekDialog`
- formularios de ventas y recogidas
- dashboard en movil
- estadisticas en movil
- badges de estados largos y bloques de actividad reciente

## 19. Endpoints principales usados por el frontend

### Auth

- `POST /login/`
- `POST /authenticate/login`
- `POST /token/refresh/`

### Perfil

- `GET /users/profile/`
- `PUT /users/profile/`
- `POST /users/set_password/`

### Operacion

- CRUD `clients`
- CRUD `workers`
- CRUD `trucks`
- CRUD `zones`
- CRUD `routes`
- `generate-week`
- `operational-overview`
- `start_route_day`
- `finish_route_day`
- `complete_stop`
- `google-navigation`
- CRUD `collections`
- `GET /collections/requests/me/`
- `POST /collections/requests/{id}/answer/`

### Bloque economico

- `GET /companies/settings/`
- `PUT /companies/settings/`
- CRUD `buyers`
- CRUD `sales`
- `GET /sales/{id}/invoice/download/`
- `GET /sales/economic-summary/`

## 20. Resumen del estado actual del frontend

- cobertura funcional principal: si
- navegacion por rol: alineada con backend
- modulo economico owner-only: integrado
- modulo de rutas: separado entre planificacion y ejecucion
- responsive: trabajado especialmente en rutas, recogidas, dashboard, configuracion y ventas
- documentacion funcional del frontend: centralizada ya en `docs` del backend

## 21. Patrones de estado de pantalla

Para mantener consistencia entre modulos, las pantallas del frontend deberian contemplar siempre estos estados:

- `loading`: skeletons, cards vacias o spinners discretos
- `empty`: mensaje contextual y CTA clara para crear o volver
- `error`: mensaje visible, no tecnico, con opcion de reintento
- `success`: feedback claro tras guardar, eliminar o descargar documentos

Esto es especialmente importante en:

- listados paginados
- modales de accion
- formularios con validacion
- vistas operativas de rutas

## 22. Convenciones de consumo de API en frontend

### 22.1 Fuente de verdad

- los importes economicos finales los calcula backend
- el frontend puede previsualizar, pero no debe imponer el calculo definitivo
- campos enriquecidos como `*_label`, `*_name` o `*_display` deben aprovecharse para reducir logica duplicada

### 22.2 Fechas y horas

- las fechas puras de negocio como `invoice_date` o `route_day.date` se tratan como fechas, no como timestamps
- los `datetime` tecnicos deben mostrarse convertidos a zona horaria de interfaz
- en movil conviene vigilar especialmente los `input[type=\"date\"]`

### 22.3 Paginacion y filtros

- los listados deben asumir paginacion del backend
- cuando exista `search`, se debe priorizar como entrada de busqueda libre
- los contadores y chips de filtro no deben romper la experiencia movil

## 23. Guards, permisos y visibilidad

La interfaz no debe limitarse a ocultar botones; debe respetar el modelo funcional completo:

- `owner`: acceso a todos los modulos de gestion y bloque economico
- `worker`: acceso operativo restringido
- `client`: portal reducido a solicitudes, historial y perfil

Implicaciones practicas:

- los items de menu se filtran por rol
- las rutas privadas deben redirigir si el rol no es valido
- las pantallas owner-only no deben confiar solo en el backend para ocultarse

## 24. Checklist responsive minima por modulo

Antes de dar una pantalla por cerrada, deberia comprobarse al menos lo siguiente:

- el header no desborda en 375px
- los contadores se pliegan o adaptan en movil
- los filtros pasan a grid o apilado en pantallas pequenas
- los modales usan scroll interno y CTA visibles
- las tablas problematicas tienen alternativa en tarjetas o scroll controlado
- los botones principales son tactiles y mantienen jerarquia visual
- los badges largos no se convierten en formas ilegibles

Este checklist es especialmente relevante para:

- dashboard
- routes list / route execution
- collections list / create / edit
- sales create / edit
- settings

## 25. Testing frontend actual

El frontend ya no depende solo de revision visual manual. Existe una base de tests por modulo con `Vitest + Testing Library`.

### Modulos actualmente cubiertos

- `workers`
  - alta sin exponer `role` ni `company`
  - edicion sin degradar perfiles ni enviar campos no permitidos
- `buyers`
  - estado vacio sin duplicidad de mensajes
- `dashboard`
  - contadores plegables en movil
  - badges largas adaptadas para estados tipo `Pendiente de medicion`
- `sales`
  - formulario con numero de factura manual y fecha operativa unica
  - detalle sin textos legacy retirados
- `collections`
  - detalle con estado `Facturable` y motivo de deduccion traducido
- `clients`
  - historial con badge `Facturable / No facturable`
- `routes`
  - `GenerateWeekDialog` con/sin regeneracion segun contexto semanal
- `settings`
  - guardado independiente por bloque
  - secciones en formato dropdown
- `stats`
  - resumen economico owner y ausencia de boton `Recargar`
  - leyendas visuales y ajuste de graficas para movil
- `trucks`
  - estado vacio del listado
- `profile`
  - el perfil `owner` no muestra atributos impropios como `Frecuencia`

### Modulos que siguen dependiendo mas de validacion manual

- `dashboard`
- `collectionZones`
- pantallas de login social
- flujo visual completo de ejecucion de ruta sobre mapa
- validacion responsive final en movil real

No porque no sean importantes, sino porque concentran mas comportamiento visual, GIS o integracion externa y conviene cubrirlos con una mezcla de test automatizado y validacion manual guiada.

## 26. Valor del frontend dentro del TFG

El frontend no es una capa decorativa del backend. En GreenPath cumple un papel funcional fuerte porque traduce procesos complejos a flujos operables:

- convierte la planificacion logistica en pantallas de detalle y ejecucion separadas
- transforma datos geograficos en mapas comprensibles para owner y worker
- adapta tablas y contadores a tarjetas y controles tocables en movil
- protege al usuario de conceptos internos como segmentos o tramos tecnicos, mostrando solo decisiones operativas claras
- permite que ventas, facturas, configuracion y estadisticas sean manejables desde una interfaz coherente

Este enfoque es importante para la defensa del TFG porque muestra que la experiencia de usuario se ha trabajado como parte del dominio, no como una capa final añadida.

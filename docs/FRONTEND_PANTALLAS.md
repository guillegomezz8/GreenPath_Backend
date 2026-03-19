# Inventario de Pantallas Frontend

Fecha de repaso: 2026-03-19

## 1. Autenticacion

### 1.1 Social login

- Ruta: `/socialLogin`
- Archivo: `src/pages/oauth/SocialLogin.jsx`
- Estado: Implementada
- Notas:
  - Login Google
  - Redireccion por rol (`client` -> `/my-requests`, resto -> `/dashboard`)

### 1.2 Login usuario/password

- Ruta: `/login`
- Archivo: `src/pages/oauth/Login.jsx`
- Estado: Implementada
- Notas:
  - Login JWT
  - Redireccion por rol via `AuthProvider`

## 2. Dashboard

- Ruta: `/dashboard`
- Archivo: `src/pages/dashboard/Dashboard.jsx`
- Estado: Implementada
- Notas:
  - Vista owner/worker con KPIs globales
  - Vista client con KPIs de solicitudes y recogidas propias
  - Acceso rapido a rutas operativas

## 3. Perfil

- Ruta: `/profile` y `/perfil`
- Archivo: `src/pages/profile/ProfilePage.jsx`
- Estado: Implementada
- Notas:
  - Edicion de datos
  - Cambio de contrasena
  - Cambio de foto si el perfil lo permite

## 4. Clientes

- Rutas:
  - `/clients`
  - `/clients/new`
  - `/clients/:id`
  - `/clients/:id/edit`
- Archivos:
  - `src/pages/clients/ClientsList.jsx`
  - `src/pages/clients/ClientCreate.jsx`
  - `src/pages/clients/ClientDetail.jsx`
  - `src/pages/clients/ClientEdit.jsx`
- Estado: Implementadas

## 5. Trabajadores

- Rutas:
  - `/workers`
  - `/workers/new`
  - `/workers/:id`
  - `/workers/:id/edit`
- Archivos:
  - `src/pages/workers/WorkersList.jsx`
  - `src/pages/workers/WorkerCreate.jsx`
  - `src/pages/workers/WorkerDetail.jsx`
  - `src/pages/workers/WorkerEdit.jsx`
- Estado: Implementadas

## 6. Camiones

- Rutas:
  - `/trucks`
  - `/trucks/new`
  - `/trucks/:id/edit`
  - `/assign-truck/:id`
- Archivos:
  - `src/pages/trucks/TrucksList.jsx`
  - `src/pages/trucks/TruckCreate.jsx`
  - `src/pages/trucks/TruckEdit.jsx`
  - `src/pages/trucks/AssignTruck.jsx`
- Estado: Implementadas

## 7. Zonas

- Ruta: `/collection-zones`
- Archivo: `src/pages/collectionZones/CollectionZonesList.jsx`
- Estado: Implementada
- Notas:
  - Alta, edicion y borrado de poligonos
  - Integracion con mapa

## 8. Rutas

- Rutas:
  - `/routes`
  - `/routes/new`
  - `/routes/:id`
  - `/routes/:id/edit`
  - `/routes/:id/execute`
- Archivos:
  - `src/pages/routes/RoutesList.jsx`
  - `src/pages/routes/RouteCreate.jsx`
  - `src/pages/routes/RouteDetail.jsx`
  - `src/pages/routes/RouteEdit.jsx`
  - `src/pages/routes/RouteExecution.jsx`
  - `src/pages/routes/RouteForm.jsx`
- Estado: Implementadas
- Notas:
  - Generacion semanal con modal compartido y responsive desde listado y detalle
  - Listado con filtros rapidos: todas / con trabajador / sin trabajador
  - Detalle orientado a planificacion semanal
  - Pantalla separada `Realizar ruta` para la operativa diaria
  - Modales de generacion, cierre y registro adaptados a movil
  - Operativa basada en mapa + panel lateral/apilado segun breakpoint

## 9. Recogidas

- Rutas:
  - `/collections`
  - `/collections/new`
  - `/collections/:id`
  - `/collections/:id/edit`
- Archivos:
  - `src/pages/collections/CollectionsList.jsx`
  - `src/pages/collections/CollectionCreate.jsx`
  - `src/pages/collections/CollectionDetail.jsx`
  - `src/pages/collections/CollectionEdit.jsx`
- Estado: Implementadas
- Notas:
  - El precio por litro se precarga desde la configuracion global de empresa
  - La edicion esta enfocada al flujo de medicion en nave
  - El detalle muestra el motivo de deduccion traducido

## 10. Compradores

- Rutas:
  - `/buyers`
  - `/buyers/new`
  - `/buyers/:id`
  - `/buyers/:id/edit`
- Archivos:
  - `src/pages/buyers/BuyersList.jsx`
  - `src/pages/buyers/BuyerCreate.jsx`
  - `src/pages/buyers/BuyerDetail.jsx`
  - `src/pages/buyers/BuyerEdit.jsx`
  - `src/pages/buyers/BuyerForm.jsx`
- Estado: Implementadas
- Notas:
  - Solo visibles para `owner`
  - Modulo interno sin acceso para el comprador
  - Filtros reforzados por ciudad, provincia y datos de contacto

## 11. Ventas

- Rutas:
  - `/sales`
  - `/sales/new`
  - `/sales/:id`
  - `/sales/:id/edit`
- Archivos:
  - `src/pages/sales/SalesList.jsx`
  - `src/pages/sales/SaleCreate.jsx`
  - `src/pages/sales/SaleDetail.jsx`
  - `src/pages/sales/SaleEdit.jsx`
  - `src/pages/sales/SaleForm.jsx`
- Estado: Implementadas
- Notas:
  - Solo visibles para `owner`
  - Numero de factura manual
  - Una sola fecha visible y operativa: `invoice_date`
  - Descarga y regeneracion de factura PDF

## 12. Configuracion de empresa

- Ruta:
  - `/settings`
- Archivo:
  - `src/pages/settings/CompanySettingsPage.jsx`
- Estado: Implementada
- Notas:
  - Solo visible para `owner`
  - Secciones en dropdown independientes:
    - precio global por litro
    - datos de facturacion
    - hub de empresa
  - Botones de guardar y restablecer por bloque
  - El logo de facturacion ya no forma parte del flujo funcional

## 13. Solicitudes de recogida (cliente)

- Ruta: `/my-requests`
- Archivo: `src/pages/collections/CollectionRequestsPage.jsx`
- Estado: Implementada
- Notas:
  - Lista por estado
  - Vista de limite de respuesta
  - Accion de responder litros para solicitudes abiertas

## 14. Estadisticas

- Ruta: `/stats`
- Archivo: `src/pages/stats/Stats.jsx`
- Estado: Implementada
- Notas:
  - Resumen economico real:
    - costes por recogidas confirmadas
    - ingresos por ventas
    - beneficio neto
    - volumen comprado vs vendido

## 15. Error

- Ruta: `*`
- Archivo: `src/pages/error/Error404.jsx`
- Estado: Implementada

## 16. Navegacion y layout

### 16.1 Sidebar por rol

- Archivo: `src/components/layout/Sidebar.jsx`
- Estado: Actualizado
- Comportamiento:
  - `owner`: menu completo, incluyendo compradores, ventas, configuracion y estadisticas
  - `worker`: menu operativo
  - `client`: dashboard + solicitudes + recogidas
  - Bloque foto/email como acceso a perfil

### 16.2 Topbar

- Archivo: `src/components/layout/Topbar.jsx`
- Estado: Actualizada
- Comportamiento:
  - Solo boton `Cerrar sesion` a la derecha
  - Sin acceso a perfil en topbar

### 16.3 MainLayout

- Archivo: `src/components/layout/MainLayout.jsx`
- Estado: Ajustado
- Notas:
  - Corregido desplazamiento de topbar con sidebar abierta

## 17. Endpoints frontend utilizados (resumen)

- Auth:
  - `POST /login/`
  - `POST /authenticate/login`
  - `POST /token/refresh/`
- Usuarios:
  - `GET/PUT /users/profile/`
  - `POST /users/set_password/`
- Rutas:
  - CRUD `routes`
  - `generate-week`
  - `operational-overview`
  - `start_route_day`
  - `finish_route_day`
  - `complete_stop`
  - `google-navigation`
- Recogidas:
  - CRUD `collections`
  - `GET /collections/requests/me/`
  - `POST /collections/requests/{id}/answer/`
- Configuracion:
  - `GET /companies/settings/`
  - `PUT /companies/settings/`
- Compradores:
  - CRUD `buyers`
- Ventas:
  - CRUD `sales`
  - `GET /sales/{id}/invoice/download/`
  - `POST /sales/{id}/invoice/regenerate/`
  - `GET /sales/economic-summary/`

## 18. Resultado del repaso

- Pantallas principales operativas: si
- Flujo economico owner-only implementado en frontend: si
- Navegacion por rol revisada y ajustada
- Configuracion y estadisticas alineadas con ventas + facturacion

# Inventario de Pantallas Frontend

Fecha de repaso: 2026-03-02

## 1. Autenticacion

## 1.1 Social login

- Ruta: `/socialLogin`
- Archivo: `src/pages/oauth/SocialLogin.jsx`
- Estado: Implementada
- Notas:
  - Login Google.
  - Redireccion por rol (`client` -> `/my-requests`, resto -> `/dashboard`).

## 1.2 Login usuario/password

- Ruta: `/login`
- Archivo: `src/pages/oauth/Login.jsx`
- Estado: Implementada
- Notas:
  - Login JWT.
  - Redireccion por rol via `AuthProvider`.

## 2. Dashboard

- Ruta: `/dashboard`
- Archivo: `src/pages/dashboard/Dashboard.jsx`
- Estado: Implementada
- Notas:
  - Vista owner/worker con KPIs globales.
  - Vista client con KPIs de solicitudes/recogidas propias.

## 3. Perfil

- Ruta: `/profile` y `/perfil`
- Archivo: `src/pages/profile/ProfilePage.jsx`
- Estado: Implementada
- Notas:
  - Edicion de datos.
  - Cambio de contraseña.
  - Cambio de foto (si perfil lo permite).
  - Boton atras eliminado (cabecera limpia).

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
  - Alta/edicion/borrado de poligonos.
  - Integracion mapa.

## 8. Rutas

- Rutas:
  - `/routes`
  - `/routes/new`
  - `/routes/:id`
  - `/routes/:id/edit`
- Archivos:
  - `src/pages/routes/RoutesList.jsx`
  - `src/pages/routes/RouteCreate.jsx`
  - `src/pages/routes/RouteDetail.jsx`
  - `src/pages/routes/RouteEdit.jsx`
  - `src/pages/routes/RouteForm.jsx`
- Estado: Implementadas
- Notas:
  - Generacion semanal con flags.
  - Ejecucion RouteDay (start/finish).
  - Modal de cierre parcial/cancelado cuando hay pendientes.
  - Dropdown de parada pendiente para registrar recogida.
  - Tabla de paradas plegable (oculta por defecto).

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

## 10. Solicitudes de recogida (cliente)

- Ruta: `/my-requests`
- Archivo: `src/pages/collections/CollectionRequestsPage.jsx`
- Estado: Implementada en este repaso
- Notas:
  - Lista por estado.
  - Vista limite de respuesta.
  - Accion responder litros para solicitudes abiertas.

## 11. Estadisticas

- Ruta: `/stats`
- Archivo: `src/pages/stats/Stats.jsx`
- Estado: Implementada

## 12. Error

- Ruta: `*`
- Archivo: `src/pages/error/Error404.jsx`
- Estado: Implementada

## 13. Navegacion y layout

## 13.1 Sidebar por rol

- Archivo: `src/components/layout/Sidebar.jsx`
- Estado: Actualizado
- Comportamiento:
  - `owner`: menu completo.
  - `worker`: menu operativo.
  - `client`: dashboard + solicitudes + recogidas.
  - Bloque foto/email como acceso a perfil.

## 13.2 Topbar

- Archivo: `src/components/layout/Topbar.jsx`
- Estado: Actualizada
- Comportamiento:
  - Solo boton `Cerrar sesion` a la derecha.
  - Sin acceso a perfil en topbar.

## 13.3 MainLayout

- Archivo: `src/components/layout/MainLayout.jsx`
- Estado: Ajustado
- Notas:
  - Corregido desplazamiento de topbar con sidebar abierta.

## 14. Endpoints frontend utilizados (resumen)

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
- Clientes, workers, trucks, zones:
  - CRUD + acciones especificas.

## 15. Resultado del repaso

- Pantallas principales operativas: si.
- Pantalla faltante detectada y completada: `Mis solicitudes`.
- Navegacion por rol revisada y ajustada.
- Flujo cliente reforzado para evitar entradas a modulos no aplicables.


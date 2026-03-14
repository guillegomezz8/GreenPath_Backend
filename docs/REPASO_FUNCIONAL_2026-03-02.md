# Repaso Funcional 2026-03-02

## 1. Objetivo del repaso

- Validar coherencia backend/frontend en flujos operativos.
- Detectar pantallas pendientes o sin cobertura real.
- Cerrar gaps visibles sin tocar tests en esta iteracion.

## 2. Cambios aplicados en este repaso

## 2.1 Frontend

- Nueva pantalla cliente:
  - `src/pages/collections/CollectionRequestsPage.jsx`
  - ruta: `/my-requests`
  - consume:
    - `GET /collections/requests/me/`
    - `POST /collections/requests/{id}/answer/`

- Ruteo:
  - `src/App.jsx`
  - ruta añadida `/my-requests`.

- Sidebar por rol:
  - `src/components/layout/Sidebar.jsx`
  - Owner: menu completo.
  - Worker: menu operativo.
  - Client: dashboard + solicitudes + recogidas.

- Dashboard por rol:
  - `src/pages/dashboard/Dashboard.jsx`
  - rama client sin llamadas globales no aplicables.
  - KPIs y acciones orientadas a cliente.

- Redireccion login:
  - `src/context/AuthProvider.jsx`
  - `client` -> `/my-requests`
  - resto -> `/dashboard`

- GuestRoute:
  - `src/routes/RolesRoutes.jsx`
  - redirect por defecto actualizado a `/dashboard`.

- Social login:
  - `src/pages/oauth/SocialLogin.jsx`
  - redireccion por rol.

## 2.2 Backend

- Hardening de queryset en clientes:
  - `apps/user/api/viewsets/client_viewset.py`
  - evita acceso a `worker_profile` cuando rol es `client`.
  - retorno seguro por rol:
    - staff/superuser -> todo.
    - client -> solo su perfil.
    - owner/worker -> empresa.
    - otros -> none.

## 2.3 Documentacion añadida

- `docs/FUNCIONAL.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/ARQUITECTURA_TECNICA.md`

## 3. Comprobaciones realizadas

- Build frontend: OK.
- Integridad de rutas frontend: actualizada.
- Consistencia de flujo cliente (solicitudes): implementada.

## 4. Cobertura funcional actual (resumen)

- Gestion maestras: clientes, workers, trucks, zonas: cubierta.
- Rutas operativas:
  - configuracion.
  - generacion semanal.
  - ejecucion diaria.
  - cierre con decision parcial/cancelada: cubierto.
- Recogidas:
  - CRUD y registro en parada: cubierto.
- Solicitudes:
  - cliente responde litros: cubierto con pantalla dedicada.
- Perfil:
  - datos, foto, password: cubierto.

## 5. Riesgos/puntos a vigilar

- Coherencia de permisos en todos los viewsets para rol `client` (quedan endpoints legacy a auditar).
- Pruebas E2E del flujo completo de ruta en entorno docker.
- Monitorizacion de tareas Celery en picos de regeneracion semanal.

## 6. Siguiente iteracion recomendada

1. Añadir tests funcionales API del flujo:
   - generate-week
   - start/complete/finish route day
   - answer/manual collection request
2. Añadir panel operativo de tareas fallidas/reintentos Celery.
3. Auditar y normalizar `get_queryset` de todos los modulos para client/worker/owner.


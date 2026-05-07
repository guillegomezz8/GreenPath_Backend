# Guia de Testing GreenPath

Fecha de revision: 2026-04-30

## 1. Objetivo del documento

Este documento centraliza la estrategia de testing del proyecto.
Su objetivo es explicar:

- que tipo de tests existen hoy
- como ejecutar la suite de backend y frontend
- que modulos estan cubiertos
- que huecos siguen dependiendo de validacion manual
- como ampliar la cobertura sin romper el estilo actual del proyecto

No sustituye a la documentacion funcional o tecnica. Su papel es servir como guia operativa para validar el sistema y evolucionar la suite con criterio.

La revision actual refleja el estado de GreenPath como plataforma completa: rutas, recogidas, ventas, compradores, configuracion, facturacion bajo demanda, permisos por rol e integraciones externas.

## 2. Estrategia actual

GreenPath usa una estrategia mixta:

- tests automatizados de backend para reglas de negocio, permisos y endpoints
- tests automatizados de frontend para reglas de UX y contratos de pantalla
- validacion manual guiada para flujos con alta carga visual, GIS o integraciones externas

La idea no es perseguir cobertura superficial, sino proteger las zonas donde una regresion tiene mas impacto:

- permisos por rol
- logica economica
- planificacion y ejecucion de rutas
- configuracion global de empresa
- experiencia owner-only en ventas y compradores

## 3. Tipos de test en el proyecto

### 3.1 Backend

Backend usa principalmente tests de Django orientados a:

- permisos
- API REST
- reglas de negocio
- integridad entre modulos

No se ha orientado la suite a snapshots ni a asserts triviales de ORM, sino a escenarios funcionales reales.

### 3.2 Frontend

Frontend usa:

- `Vitest`
- `@testing-library/react`
- `@testing-library/user-event`

La suite se centra en:

- formularios
- payloads enviados a API
- visibilidad de estados
- presencia o ausencia de elementos segun reglas de negocio
- regresiones de UX ya detectadas en el proyecto

### 3.3 Validacion manual

Algunos flujos siguen necesitando validacion manual guiada porque mezclan:

- mapas
- dibujo GIS
- integraciones con Google
- generacion real de PDF
- responsive fino en movil real

Eso no significa que esten sin cubrir; significa que la estrategia correcta para ellos no es solo test unitario.

## 4. Estructura actual de tests

### 4.1 Backend

Ubicaciones principales:

- `apps/auth/tests/`
- `apps/base/tests.py`
- `apps/base/test_utils.py`
- `apps/company/tests/`
- `apps/truck/tests/`
- `apps/zone/tests/`
- `apps/user/tests/`
- `apps/collection/tests/`
- `apps/route/tests/`
- `apps/sale/tests/`

Helper comun destacado:

- `apps/base/test_utils.py`

Ese helper permite levantar contexto reusable de:

- empresa
- owner
- worker
- client
- buyer
- truck
- zone
- API client autenticado

### 4.2 Frontend

Ubicaciones actuales:

- `src/pages/workers/__tests__/`
- `src/pages/buyers/__tests__/`
- `src/pages/sales/__tests__/`
- `src/pages/collections/__tests__/`
- `src/pages/clients/__tests__/`
- `src/components/routes/__tests__/`
- `src/pages/settings/__tests__/`
- `src/pages/stats/__tests__/`
- `src/pages/trucks/__tests__/`
- `src/pages/profile/__tests__/`

La convencion actual es:

- tests junto al modulo correspondiente
- un fichero por pantalla o componente relevante
- mocks locales de `useAuth`, `useSnackbar`, `useNavigate` y API cuando hace falta

## 5. Cobertura backend actual

La suite backend valida hoy, al menos, estos bloques:

### 5.1 Auth y base

- login con credenciales
- login social con payload invalido
- utilidades base
- permisos dedicados

### 5.2 Company

- lectura y actualizacion de `CompanySettings`
- guardado de hub
- restricciones owner/worker

### 5.3 Truck

- asignacion de conductor
- reasignacion al mover conductor entre camiones
- restricciones de acceso

### 5.4 Zone

- creacion de zonas
- busqueda
- permisos

### 5.5 User

- creacion de trabajador forzando rol `worker`
- imposibilidad de degradar `owner`
- bloqueo de cambio de `company` por API de workers
- historial economico de cliente

### 5.6 Collection

- respuesta del cliente a `CollectionRequest`
- filtro `billable`

### 5.7 Route

- `generate-week`
- creacion de `RouteDay`
- creacion de `RouteDayClient`
- creacion de `CollectionRequest`
- frecuencia y planificacion por empresa sin mezclar historico ajeno
- calculo de `operational_plan` por capacidad diaria
- exportacion de Google Maps con retornos al hub entre tramos cuando aplica
- cierre de jornada con decision obligatoria si hay pendientes

### 5.8 Sale

- creacion de compradores
- ventas con numero de factura manual
- descarga de factura PDF generada bajo demanda
- resumen economico
- restricciones owner-only

## 6. Cobertura frontend actual

La suite frontend valida hoy estos puntos:

### 6.1 Workers

- `WorkerCreate` no expone `role` ni `company`
- `WorkerEdit` no envia `role`, `company`, `username` ni `user`
- un `owner` se presenta como `Propietario` y no se degrada por la UI

### 6.2 Buyers

- `BuyersList` muestra el estado vacio una sola vez

### 6.3 Sales

- `SaleForm` usa numero de factura manual
- `SaleForm` muestra el numero de la ultima factura como placeholder en alta
- `SaleForm` usa solo `Fecha de factura`
- `SaleForm` usa `kg` como unidad por defecto
- `SaleForm` permite reusar conceptos desde modal en alta y edicion
- `SaleForm` al reusar concepto no modifica la unidad seleccionada
- `SaleDetail` ya no muestra textos legacy retirados

### 6.4 Collections

- `CollectionDetail` muestra `Facturable / No facturable`
- `CollectionDetail` muestra el motivo de deduccion traducido

### 6.5 Clients

- `ClientDetail` muestra correctamente las badges facturables en historial

### 6.6 Routes

- `GenerateWeekDialog` oculta o muestra `Regenerar paradas existentes` segun el contexto semanal
- `RouteExecution` fija la semana operativa actual por defecto
- la UX operativa no expone tarjetas tecnicas de tramo aunque mantenga logica interna de capacidad

### 6.7 Settings

- `CompanySettingsPage` guarda precio de forma independiente
- `CompanySettingsPage` guarda facturacion de forma independiente
- las secciones se comportan como dropdown

### 6.8 Stats

- `Stats` muestra resumen economico owner
- `Stats` no muestra el antiguo boton de recarga
- `Stats` incorpora leyendas visuales por color
- `Stats` mantiene scroll horizontal controlado en charts estrechos

### 6.9 Trucks

- `TrucksList` muestra correctamente el estado vacio

### 6.10 Profile

- `ProfilePage` no muestra `Frecuencia` en perfiles `owner`

## 7. Estado cuantitativo actual

Snapshot validado en esta revision:

- backend: `31` tests verdes
- frontend: `17` tests verdes

Estas cifras no representan cobertura total de lineas, sino volumen de escenarios utiles ya protegidos.

## 8. Como ejecutar tests de backend

### 8.1 Opcion recomendada dentro del contenedor backend

```bash
python manage.py test apps.auth.tests apps.base.tests apps.company.tests apps.truck.tests apps.zone.tests apps.user.tests apps.collection.tests apps.route.tests apps.sale.tests
```

### 8.2 Checks complementarios recomendados

```bash
python manage.py check
python manage.py check --tag admin
python manage.py makemigrations --check --dry-run
```

### 8.3 Cuando no conviene usar el host local

En Windows host, el backend puede fallar fuera de Docker si no estan presentes dependencias GIS como GDAL.
Por eso la ruta recomendada para validar backend sigue siendo Docker.

## 9. Como ejecutar tests de frontend

### 9.1 Opcion normal

```bash
npm run test
```

### 9.2 Opcion recomendada si el `node_modules` local da problemas

En este proyecto ya ha ocurrido que el entorno local de Node quede inconsistente.
En ese caso, la via mas estable es un contenedor temporal:

```bash
docker run --rm -v "e:\\TFG\\front\\GreenPath_Frontend:/src" node:22 bash -lc "mkdir -p /tmp/app && cd /src && tar --exclude=node_modules -cf - . | (cd /tmp/app && tar -xf -) && cd /tmp/app && npm install --silent && npm run test"
```

Ventajas de este enfoque:

- entorno limpio en cada ejecucion
- no depende del `node_modules` del host
- evita falsos negativos por librerias instaladas a medias

## 10. Convenciones para ampliar la suite

### 10.1 Backend

Recomendaciones:

- crear tests por modulo, no en un archivo gigante
- usar `BackendTestMixin` para no duplicar contexto
- testear reglas de negocio, no solo serializacion
- nombrar tests con el comportamiento esperado

Patron recomendado:

- `test_owner_can_...`
- `test_worker_cannot_...`
- `test_generate_week_creates_...`

### 10.2 Frontend

Recomendaciones:

- ubicar tests junto al modulo bajo `__tests__`
- mockear solo lo necesario
- preferir asserts visibles para usuario o payloads reales
- evitar snapshots grandes de pantallas enteras

Patron recomendado:

- renderizar pantalla
- simular una accion real
- comprobar DOM o payload de API

### 10.3 Que no conviene hacer

- tests que solo comprueban que un componente renderiza
- tests acoplados a clases CSS irrelevantes
- snapshots gigantes de pantallas enteras
- mocks excesivos que ya no prueban el comportamiento real

## 11. Flujos que siguen pidiendo validacion manual

Aunque la suite ya protege bastante, conviene seguir revisando manualmente:

- `RouteExecution` con mapa real
- `CollectionZonesList` y dibujo de poligonos
- generacion y descarga visual de facturas PDF
- login social real con Google
- responsive fino en movil real
- integraciones con Gmail API y Google Directions

## 12. Siguientes prioridades razonables de testing

Si se quiere seguir ampliando cobertura, el orden mas rentable seria:

1. `dashboard`
2. `collectionZones`
3. flujos completos de `RouteExecution` con mapa y cierre parcial/cancelado
4. pruebas mas profundas de PDF/factura
5. pruebas E2E de rutas y ventas

## 13. Checklist minima antes de dar una entrega por estable

### Backend

- `manage.py check`
- `manage.py check --tag admin`
- `manage.py makemigrations --check --dry-run`
- suite de tests verde

### Frontend

- `npm run build`
- suite de tests verde

### Manual

- login por rol
- generar semana
- ejecutar una jornada
- confirmar una recogida
- crear venta y descargar factura
- revisar stats economicas

## 14. Conclusion

GreenPath ya no depende solo de pruebas manuales puntuales.
La base actual de tests protege los flujos mas sensibles y deja identificadas las zonas que por su naturaleza visual, geografica o externa requieren validacion manual complementaria. Para el TFG esto es relevante porque demuestra una estrategia de calidad realista: automatizar reglas de negocio y contratos criticos, y validar manualmente aquello que depende de mapas, proveedores externos o comportamiento responsive en dispositivo.
Existe una base automatizada suficiente para detectar regresiones importantes en:

- permisos
- rutas
- recogidas
- settings
- ventas
- resumen economico

El siguiente salto natural ya no es empezar a testear, sino ampliar con criterio la cobertura sobre mapas, E2E y flujos mas largos.

# Analisis profundo de generacion y optimizacion de rutas

Fecha de revision: 2026-05-27

## 1. Objetivo

Este documento analiza en profundidad como GreenPath genera, ordena, optimiza y ejecuta rutas operativas.

El foco principal esta en:

- generacion semanal de `RouteDay`
- seleccion de clientes y creacion de `RouteDayClient`
- calculo de capacidad y litros previstos
- optimizacion con Google Directions
- creacion y programacion de `CollectionRequest`
- uso del plan operativo en frontend
- riesgos tecnicos y mejoras recomendadas

El analisis se ha hecho sobre el codigo actual, no solo sobre documentacion existente.

Esta revision tambien alinea el documento con el enfoque actual del TFG: rutas como nucleo logistico de la plataforma, segmentacion por capacidad tratada como logica interna, mapa operativo simplificado para el usuario y dependencia controlada de Google Maps, Celery, Redis y PostGIS.

Tambien separa tres conceptos que conviene no mezclar:

- seleccion de paradas: decide que clientes entran en cada jornada
- optimizacion de orden: decide en que secuencia se visitan las paradas ya seleccionadas
- navegacion externa: construye enlaces de Google Maps para ejecutar el orden guardado

La idea de producto actual es que los conceptos tecnicos internos no se trasladen de forma cruda al usuario. El backend puede trabajar con segmentos, carga acumulada y retornos a hub, pero la interfaz debe presentar decisiones operativas sencillas: siguiente parada, volver a nave cuando toque, registrar recogida y finalizar jornada.

## 2. Archivos revisados

Backend:

- `apps/route/models.py`
- `apps/route/utils.py`
- `apps/route/api/viewsets/route_viewset.py`
- `apps/route/api/serializers/route_serializers.py`
- `apps/route/tests/test_route_api.py`
- `apps/collection/models.py`
- `apps/company/models.py`
- `apps/user/models/client.py`
- `apps/zone/models.py`
- `apps/truck/models.py`
- `apps/base/enums.py`
- `apps/base/literals.py`

Frontend:

- `src/pages/routes/RouteForm.jsx`
- `src/pages/routes/RouteDetail.jsx`
- `src/pages/routes/RouteExecution.jsx`
- `src/components/routes/GenerateWeekDialog.jsx`
- `src/components/routes/RouteDayMap.jsx`
- `src/components/routes/__tests__/GenerateWeekDialog.test.jsx`

Documentacion relacionada:

- `docs/ROUTE_FLOW.md`
- `docs/FUNCIONAL.md`
- `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`

## 3. Mapa general del sistema de rutas

El modulo tiene dos niveles:

- plantilla de ruta: `Route`
- jornada operativa concreta: `RouteDay`

La plantilla define:

- empresa
- trabajador asignado
- fecha de inicio y fecha de fin opcional
- dia inicial y final de semana operativa
- configuracion de zonas por weekday mediante `RouteZoneDay`

La jornada concreta representa:

- una fecha real
- un estado operativo
- capacidad diaria en litros
- lista ordenada de paradas mediante `RouteDayClient`
- solicitudes previas al cliente mediante `CollectionRequest`
- recogidas reales mediante `Collection`

El flujo normal es:

1. El owner crea una ruta.
2. El owner configura zonas por dia.
3. El owner genera una semana operativa.
4. El backend crea o reutiliza `RouteDay`.
5. El backend selecciona clientes por zona, empresa y frecuencia.
6. El backend crea `RouteDayClient`.
7. El backend intenta optimizar el orden con Google.
8. El backend crea o actualiza `CollectionRequest`.
9. El frontend consume `operational-overview`.
10. El worker u owner ejecuta la jornada.
11. Cada parada genera una `Collection`.
12. La jornada se finaliza como completada, parcial o cancelada.

## 4. Modelo de datos implicado

### 4.1 `Route`

Es la plantilla de planificacion.

Campos clave:

- `name`
- `company`
- `worker`
- `start_date`
- `end_date`
- `week_start`
- `week_end`

Observaciones:

- Actualmente la ruta tiene un unico trabajador asignado.
- La capacidad no vive en `Route`; se resuelve por `RouteDay` o por camion del trabajador.
- `week_start` y `week_end` permiten semanas operativas no necesariamente de lunes a domingo.

### 4.2 `RouteZoneDay`

Relaciona una ruta con zonas para un dia de la semana.

Campos clave:

- `route`
- `weekday`
- `zones`

Restriccion:

- unico por `(route, weekday)`

Uso:

- la generacion busca el `RouteZoneDay` correspondiente al weekday de cada fecha
- si no existe o no tiene zonas, ese dia no genera paradas

### 4.3 `RouteDay`

Representa una jornada concreta.

Campos clave:

- `route`
- `date`
- `status`
- `daily_capacity_liters`
- `started_at`
- `finished_at`

Restriccion:

- unico por `(route, date)`

Estados:

- `PLANNED`
- `IN_PROGRESS`
- `COMPLETED`
- `PARTIAL`
- `CANCELED`

### 4.4 `RouteDayClient`

Representa una parada planificada.

Campos clave:

- `route_day`
- `client`
- `order`

Restricciones:

- unico por `(route_day, order)`
- unico por `(route_day, client)`

Estas restricciones son importantes porque obligan a que una jornada no tenga dos paradas con el mismo orden ni dos paradas para el mismo cliente.

### 4.5 `CollectionRequest`

Es la solicitud previa al cliente para confirmar envases y calcular litros equivalentes.

Campos clave:

- `route_day_client`
- `expires_at`
- `status`
- `container_type`
- `container_number`
- `estimated_liters`
- `final_liters`
- `final_source`
- `auto_estimate_task_id`
- `auto_estimate_scheduled_at`

Relacion:

- `OneToOne` con `RouteDayClient`

### 4.6 `Collection`

Es la recogida real.

Campos clave:

- `client`
- `route_day_client`
- `worker`
- `collection_date`
- `container_type`
- `container_number`
- `estimated_liters`
- `measured_liters`
- `deduction_liters`
- `net_liters`
- `price_per_liter`
- `billable`
- `total_price`
- `status`

Restriccion:

- solo puede existir una recogida activa no cancelada por `route_day_client`

## 5. Endpoints principales

### 5.1 Crear y configurar ruta

- `POST /routes/`
- `PUT /routes/{id}/`
- `GET /routes/{id}/zone-config/`
- `PUT /routes/{id}/zone-config/`

Responsabilidad:

- crear la plantilla
- asignar trabajador
- asignar zonas por dia

### 5.2 Generar semana

- `POST /routes/{id}/generate-week/`

Es el endpoint principal moderno.

Responsabilidad:

- crear o reutilizar `RouteDay`
- generar paradas
- aplicar capacidad
- optimizar con Google si procede
- crear solicitudes

### 5.3 Consultar vista operativa

- `GET /routes/{id}/operational-overview/`

Responsabilidad:

- devolver datos de ruta
- devolver zonas configuradas
- devolver jornadas de la semana
- devolver paradas, solicitudes y recogidas
- devolver `operational_plan`

### 5.4 Ejecutar jornada

- `POST /routes/{id}/route-days/{route_day_id}/start/`
- `POST /routes/{id}/route-days/{route_day_id}/finish/`
- `POST /routes/{id}/route-days/{route_day_id}/stops/{route_day_client_id}/complete/`
- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

### 5.5 Endpoint antiguo por rango

El endpoint legacy `POST /routes/{id}/generate-range-routes/` se ha eliminado porque no era consumido por el frontend y no seguia las mismas garantias que `generate-week`.

## 6. Validacion de entrada de `generate-week`

Serializer:

- `GenerateWeekSerializer`

Payload principal:

```json
{
  "week_start_date": "2026-04-20",
  "daily_capacity_liters": "500.00",
  "regenerate": false,
  "auto_estimate_without_contact": false,
  "max_clients_per_day": 10
}
```

Modo alternativo por dias:

```json
{
  "week_start_date": "2026-04-20",
  "days": [
    { "date": "2026-04-20", "daily_capacity_liters": "500.00" },
    { "date": "2026-04-21", "daily_capacity_liters": "700.00" }
  ]
}
```

Reglas:

- `week_start_date` es obligatorio.
- Debe venir `daily_capacity_liters` global o `days`.
- No se pueden enviar ambos modos a la vez.
- `days` no puede tener fechas duplicadas.
- Las fechas de `days` deben caer dentro de la semana iniciada en `week_start_date`.
- `max_clients_per_day` tiene minimo 1 y maximo 100.
- `daily_capacity_liters` acepta valor 0, que en la practica desactiva el filtro de capacidad.

Observacion de frontend:

- `RouteDetail.jsx` solo envia capacidad global.
- El frontend actual no expone el modo avanzado `days[]`.
- El frontend tampoco envia `max_clients_per_day`, por lo que backend aplica el valor por defecto.

## 7. Generacion semanal moderna

Funcion:

- `generate_week_for_route(...)`

Firma:

```python
generate_week_for_route(
    route,
    week_start_date,
    regenerate=False,
    daily_capacity_liters=None,
    days=None,
    auto_estimate_without_contact=False,
    max_clients_per_day=10,
    optimize_with_google=True,
)
```

### 7.1 Proteccion contra concurrencia

Antes de generar, crea un lock en cache:

```text
route_week_generation_lock_{route.id}_{week_start_date}
```

Caracteristicas:

- timeout de 300 segundos
- si ya existe, lanza error de generacion en curso
- al terminar, borra el lock en `finally`

Ademas:

- la funcion esta dentro de `transaction.atomic`
- recarga la ruta con `select_for_update`

Esto reduce el riesgo de doble generacion simultanea para la misma ruta y semana.

Punto de atencion:

- la llamada a Google se hace dentro del flujo transaccional, por lo que una respuesta lenta puede mantener locks de base de datos mas tiempo del ideal.

### 7.2 Validacion de rango de fechas

El backend calcula:

```text
week_end_date = week_start_date + 6 dias
```

La semana se rechaza si queda completamente fuera del rango de la ruta:

- `week_end_date < route.start_date`
- `week_start_date > route.end_date`, si existe `end_date`

Si la semana se solapa parcialmente con la vigencia, no se rechaza entera. El bucle saltara los dias fuera de rango.

### 7.3 Dias operativos habilitados

Cada fecha se evalua con:

- `_is_route_date_in_range(route, target_date)`
- `_is_weekday_enabled(route, weekday)`

`_is_weekday_enabled` soporta rangos normales y rangos que cruzan domingo.

Ejemplos:

- lunes a viernes: `week_start=0`, `week_end=4`
- viernes a martes: `week_start=4`, `week_end=1`

### 7.4 Creacion o reutilizacion de `RouteDay`

Para cada dia valido:

```python
route_day, _ = RouteDay.objects.get_or_create(route=locked_route, date=target_date)
```

Despues decide si se puede modificar.

Una jornada se considera no mutable si:

- tiene `started_at`
- tiene `finished_at`
- tiene alguna `Collection`
- su estado no es `PLANNED` ni `CANCELED`

Si no es mutable:

- se preserva
- no se regeneran paradas
- sus clientes se anaden al conjunto semanal para evitar duplicados

### 7.5 Regeneracion

Si `regenerate=true`, antes de tocar la semana se llama a:

- `_ensure_week_regeneration_allowed(...)`

Esta funcion revisa todos los `RouteDay` de la semana.

Si alguno no es mutable:

- se bloquea la regeneracion completa
- se evita destruir trazabilidad operativa

Cuando una jornada mutable se regenera:

- se revocan tasks de solicitudes existentes
- se borran sus `RouteDayClient`
- se vuelve a calcular desde cero

### 7.6 Control de duplicados semanales

El sistema mantiene:

```python
week_assigned_client_ids
```

Objetivo:

- evitar que el mismo cliente aparezca dos veces en la misma semana de la misma ruta

Comportamiento:

- sin regenerar, parte de los clientes ya asignados esa semana
- al procesar un dia, excluye clientes ya reservados en otros dias
- si el dia ya tenia ese cliente, no lo trata como duplicado propio

Esto evita que una zona compartida en varios dias meta al mismo cliente repetido en la misma semana.

## 8. Asignacion de capacidad

La capacidad puede venir de tres sitios, en orden practico:

1. `daily_capacity_liters` enviado al generar la semana.
2. `days[]` con capacidad por fecha.
3. capacidad del camion asociado al trabajador de la ruta.

La resolucion por defecto se hace con:

- `_resolve_route_default_capacity_liters(route)`
- `resolve_route_day_capacity_liters(route_day)`
- `_ensure_route_day_capacity_liters(route_day)`

La capacidad por defecto mira:

```text
route.worker.truck.capacity_liters
```

Si existe, se asigna al `RouteDay`.

Si no existe:

- `daily_capacity_liters` puede quedar `None`
- el filtro de capacidad puede no aplicarse

Punto importante:

- si capacidad es `0`, el filtro de capacidad no limita, porque la condicion es `capacity_limit > 0`

## 9. Generacion de paradas por dia

Funcion:

- `generate_route_day_clients(...)`

Firma:

```python
generate_route_day_clients(
    route_day,
    regenerate=False,
    reserved_client_ids=None,
    auto_estimate_without_contact=False,
    optimize_with_google=True,
    max_clients_per_day=MAX_CLIENTS_PER_DAY,
)
```

### 9.1 Validacion de mutabilidad

La primera barrera es:

- `_is_route_day_generation_mutable(route_day)`

Si no es mutable:

- con `regenerate=True`, lanza error
- sin regenerar, devuelve las paradas existentes y no toca nada

### 9.2 Zonas del dia

Busca:

```python
RouteZoneDay.objects.filter(
    route=route_day.route,
    weekday=route_day.weekday,
)
```

Si no hay configuracion:

- no genera paradas

Si hay configuracion pero sin zonas:

- no genera paradas

Si las zonas no tienen geometria:

- no genera paradas

### 9.3 Filtro espacial

Construye un OR de filtros:

```python
Q(location__within=zone.polygon)
```

Despues filtra clientes:

```python
Client.objects
  .filter(companies=route_day.route.company, location__isnull=False)
  .filter(spatial_q)
```

Reglas:

- solo clientes de la empresa
- solo clientes con coordenadas
- solo clientes dentro de alguna zona asignada al dia

Punto de atencion:

- `within` puede dejar fuera puntos exactamente en el borde del poligono, segun comportamiento GIS. Si aparecen clientes "pegados" al borde que no entran, conviene revisar si `covers` o un buffer pequeno seria mas adecuado.

### 9.4 Historico usado

El queryset anota:

- `last_collection_date`
- `last_planned_date`

`last_collection_date`:

- maxima fecha de recogida anterior
- excluye canceladas
- acotada a la misma empresa

`last_planned_date`:

- maxima fecha planificada anterior
- excluye jornadas canceladas
- acotada a la misma empresa

La funcion de ambito empresarial es:

```python
_collection_scope_for_company(company)
```

Regla:

- una recogida cuenta para la empresa si viene de una ruta de esa empresa
- o si es manual y el worker pertenece a esa empresa

Esto es relevante para clientes compartidos entre empresas.

### 9.5 Frecuencia de recogida

Funcion:

- `_is_client_due(client, target_date, last_collection_date, last_planned_date)`

Frecuencias:

- `WEEKLY`: 7 dias
- `2_WEEKS`: 14 dias
- `3_WEEKS`: 21 dias
- `4_WEEKS`: 28 dias

Referencia usada:

- ultima recogida real
- o ultima planificacion previa si es posterior

Si no hay referencia:

- el cliente entra como pendiente de recogida

### 9.6 Orden base antes de Google

Los clientes candidatos se ordenan por:

```python
(
    _effective_reference_date(item) is not None,
    _effective_reference_date(item) or route_day.date,
    item.id,
)
```

Efecto:

- clientes sin referencia previa van primero
- despues clientes con referencia mas antigua
- desempate por id

La fecha efectiva es:

- ultima recogida real
- o ultima planificacion previa si es posterior

Esto alinea la prioridad inicial con la misma referencia usada para decidir si el cliente esta pendiente por frecuencia.

### 9.7 Calculo de litros previstos para insertar paradas

Funcion:

- `_planned_liters_by_client_for_company(company, client_ids)`

Prioridad:

1. media de `Collection.net_liters` confirmadas
2. media de `Collection.estimated_liters` no canceladas
3. `60.00` litros por defecto

El resultado se usa para decidir si una parada cabe en la capacidad diaria.

### 9.8 Aplicacion de limite de clientes

Variable:

- `max_clients_per_day`

Comportamiento:

- si `max_clients_per_day > 0`
- y el numero de clientes existentes ya alcanza el limite
- se corta la insercion de nuevas paradas

Valor por defecto:

- `10` en el flujo moderno

Nota:

- el serializer admite hasta `100`
- el frontend actual no expone este campo

### 9.9 Aplicacion de capacidad diaria

El sistema calcula:

```python
current_planned_liters = suma(_planned_stop_liters(row) para paradas existentes)
```

Para cada cliente candidato:

```python
if capacity_limit > 0 and current_planned_liters + planned_liters > capacity_limit:
    skip
```

Comportamiento:

- si una parada no cabe, se omite
- el sistema sigue probando los siguientes clientes
- no genera automaticamente otro `RouteDay` para el excedente
- no crea un segundo viaje persistente

Consecuencia:

- puede haber clientes que no entren en la semana por capacidad
- esos clientes podrian entrar en otra semana o si se aumenta capacidad

### 9.10 Insercion

Cada parada se crea con:

```python
RouteDayClient.objects.create(
    route_day=route_day,
    client=client,
    order=next_order,
)
```

`next_order` parte del maximo orden actual + 1.

Esto permite anadir nuevas paradas a una jornada ya existente sin rehacer las anteriores, siempre que no se regenere.

## 10. Optimizacion con Google Directions

Funcion principal actual:

- `optimize_route_day_with_google(route_day, planned_liters_by_row=None)`

Se llama desde:

- `generate_route_day_clients(...)`

La optimizacion actual es una optimizacion de orden de paradas ya seleccionadas. No decide que clientes entran, no reparte clientes entre varios trabajadores y no resuelve un VRP completo.

### 10.1 Condiciones para intentar optimizar

La optimizacion se omite si:

- hay menos de 2 paradas en la jornada
- hay menos de 2 paradas con ubicacion
- no hay hub de empresa con `location`
- no hay `GOOGLE_MAPS_API_KEY`

En esos casos:

- se conserva el orden actual
- se escribe log
- la generacion no falla

### 10.2 Segmentacion previa por capacidad

Antes de llamar a Google, el backend divide la jornada en segmentos con:

- `RouteDay.daily_capacity_liters`
- litros previstos por parada
- orden actual de `RouteDayClient`

Funcion implicada:

- `_split_route_day_clients_by_capacity(...)`

Regla:

- si la siguiente parada supera la capacidad acumulada del segmento, se abre un nuevo segmento
- si la capacidad es `0` o `None`, se considera sin limite y se optimiza un unico segmento
- si una parada individual supera la capacidad, queda igualmente en un segmento propio

Este diseno modela retornos implicitos al hub sin crear todavia entidades persistentes de subviaje o descarga.

### 10.3 Construccion de la peticion

Para cada segmento con al menos 2 paradas ubicadas:

Origen:

- `CompanyHub.location`

Destino:

- el mismo `CompanyHub.location`

Waypoints:

- todas las paradas ubicadas del segmento

Parametro:

```text
waypoints=optimize:true|lat,lng|lat,lng|...
```

Endpoint:

```text
https://maps.googleapis.com/maps/api/directions/json
```

Observacion importante:

- el codigo actual no usa como destino la parada mas lejana
- Google optimiza la lista completa de waypoints con salida y vuelta al hub

### 10.4 Paradas sin ubicacion

La generacion automatica solo selecciona clientes con ubicacion, pero pueden existir paradas sin coordenadas por datos legacy o carga manual.

En optimizacion:

- se excluyen de la llamada a Google
- se conservan en su posicion relativa dentro del segmento
- las paradas con ubicacion se reinsertan en los huecos disponibles

Ejemplo conceptual:

```text
Antes:       A(ubicada) -> B(sin ubicacion) -> C(ubicada)
Google:      C -> A
Resultado:   C -> B(sin ubicacion) -> A
```

### 10.5 Interpretacion de respuesta

Google devuelve:

```json
{
  "routes": [
    {
      "waypoint_order": [ ... ]
    }
  ]
}
```

El backend:

1. valida que `waypoint_order` tenga tantos indices como paradas ubicadas del segmento
2. valida que todos los indices sean enteros dentro de rango
3. reordena las paradas ubicadas
4. fusiona el resultado con las paradas sin ubicacion
5. actualiza `RouteDayClient.order`

### 10.6 Actualizacion segura del orden

Debido a la restriccion unica `(route_day, order)`, no se pueden intercambiar ordenes directamente.

El codigo hace dos fases:

1. mueve filas cambiadas a ordenes temporales altos
2. escribe los ordenes finales

Esto evita colisiones de unicidad durante el `bulk_update`.

### 10.7 Fallback

Si Google falla:

- error de red
- timeout
- status HTTP no valido
- JSON sin rutas
- respuesta sin `waypoint_order` valido
- longitud o indices inconsistentes

El backend:

- conserva el orden del segmento afectado
- no rompe la generacion completa
- deja logs de aviso o error

Este comportamiento es correcto para no hacer depender la operativa diaria de una integracion externa.

### 10.8 Que optimiza y que no optimiza

Optimiza:

- orden de visita dentro de cada segmento de capacidad
- recorrido circular hub -> paradas -> hub
- segmentos independientes cuando hay retorno a nave

No optimiza:

- seleccion de clientes candidatos
- reparto entre varios trabajadores o camiones
- ventanas horarias de clientes
- tiempo de servicio por parada
- turnos del trabajador
- costes economicos reales
- prediccion de trafico por hora
- reasignacion automatica de clientes omitidos por capacidad

## 11. Plan operativo por capacidad

Funcion:

- `build_route_day_operational_plan(route_day, ordered_clients=None)`

Objetivo:

- dividir una jornada en segmentos logicos segun capacidad
- calcular carga planificada y carga registrada
- determinar si hay que volver al hub
- sugerir la parada activa

### 11.1 Litros previstos por parada

Funcion:

- `_planned_stop_liters(row)`

Prioridad:

1. `CollectionRequest.final_liters`
2. `CollectionRequest.estimated_liters`
3. calculo por envase y numero de envases
4. `0.00`

Este calculo se usa para plan operativo y navegacion, no para seleccion inicial de clientes.

### 11.2 Creacion de segmentos

Para cada parada ordenada:

- calcula litros previstos
- mira si hay recogida asociada
- mira si la recogida esta cancelada
- si anadir la parada supera capacidad, cierra segmento y abre otro

Condicion de corte:

```python
current_segment["planned_load_liters"] > 0
and current_segment["planned_load_liters"] + stop_liters > capacity_limit
```

Punto importante:

- si una sola parada supera la capacidad diaria, se mete igualmente en un segmento propio.
- el sistema no bloquea esa situacion en el plan operativo.

### 11.3 Metricas expuestas

El resultado incluye:

- `capacity_liters`
- `planned_load_liters`
- `registered_load_liters`
- `segments_count`
- `returns_to_hub_count`
- `requires_hub_return`
- `active_segment_number`
- `active_segment_route_day_client_id`
- `active_segment_current_load_liters`
- `active_segment_remaining_capacity_liters`
- `segments`

Cada segmento incluye:

- numero de segmento
- litros previstos
- litros cargados actualmente
- paradas planificadas
- paradas registradas
- paradas completadas
- paradas canceladas
- paradas pendientes
- ids de paradas
- ordenes

### 11.4 Como cuenta una parada cancelada

Una recogida cancelada:

- cuenta como registrada
- cuenta como cancelada
- no suma carga registrada no cancelada

Esto permite cerrar una jornada como completada si todas las paradas estan gestionadas, aunque algunas hayan sido canceladas.

### 11.5 Parada activa

El segmento activo es:

- el primer segmento con paradas pendientes
- si no hay pendientes, el ultimo segmento

La parada activa es:

- `first_pending_route_day_client_id` del segmento activo

Frontend usa esto para proponer la siguiente parada.

## 12. Navegacion Google desde la ejecucion

Funcion:

- `get_route_day_google_navigation_url(route_day)`

Endpoint:

- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`

### 12.1 Validaciones

Se exige:

- al menos una parada con ubicacion
- hub de empresa con ubicacion

Si falta algo:

- lanza `ValueError`
- el endpoint devuelve 400

### 12.2 Construccion de URL

Origen:

- hub

Destino:

- hub

Waypoints:

- paradas en orden
- hub intermedio entre segmentos si hay retornos por capacidad

Ejemplo conceptual:

```text
hub -> parada 1 -> parada 2 -> hub -> parada 3 -> parada 4 -> hub
```

URL:

```text
https://www.google.com/maps/dir/?api=1&origin=...&destination=...&travelmode=driving&waypoints=...
```

Si el numero de waypoints supera el limite interno conservador, el backend divide la navegacion en varios enlaces:

- mantiene `url` con el primer enlace por compatibilidad
- devuelve `urls[]` con todos los tramos
- devuelve `is_split=true` cuando hay mas de un enlace

El frontend abre todos los enlaces en escritorio. En movil abre el primero, porque la navegacion se delega a la app o navegador del dispositivo.

### 12.3 Diferencia entre optimizacion y navegacion

Optimizacion:

- se usa al generar semana
- llama a Google Directions API
- reordena `RouteDayClient.order`

Navegacion:

- se usa en ejecucion diaria
- genera URL de Google Maps
- no reordena nada
- respeta el orden ya guardado
- inserta retornos al hub segun `operational_plan`

## 13. CollectionRequest y tareas automaticas

Cada parada debe tener una solicitud asociada.

Funcion:

- `_schedule_collection_request(route_day_client, route_day_start, auto_estimate_without_contact=False)`

### 13.1 Fecha limite

Se calcula:

```text
expires_at = inicio del route_day - 36 horas
```

`inicio del route_day` se toma como:

```text
fecha del dia a las 00:00 en timezone actual
```

Ejemplo:

- route_day: lunes 2026-04-20 00:00
- expires_at: sabado 2026-04-18 12:00

### 13.2 Creacion idempotente

Busca con `select_for_update`.

Si no existe:

- crea `CollectionRequest`

Si otro proceso la creo a la vez:

- captura `IntegrityError`
- vuelve a leerla

### 13.3 Autoestimacion normal

Si la solicitud esta `PENDING`:

- genera `task_id`
- guarda `auto_estimate_task_id`
- programa Celery en `expires_at`
- si ya vencio, ejecuta inmediatamente

Si cambia la expiracion:

- revoca task anterior
- programa task nueva

### 13.4 Notificacion

Solo se notifica cuando la solicitud es nueva.

Antes revisa:

- `GMAIL_FROM`
- `GMAIL_TOKEN_JSON`
- `GMAIL_CLIENT_SECRET_JSON`

Si Gmail no esta configurado:

- no notifica
- no rompe la generacion

Tambien usa cache para evitar encolar notificaciones duplicadas rapidamente.

### 13.5 Autoestimacion sin contacto

Si `auto_estimate_without_contact=True`:

- no notifica al cliente
- revoca task anterior si existia
- si la solicitud ya estaba `ANSWERED` o `MANUAL`, la conserva
- si no, calcula litros automaticamente
- marca estado como `AUTO_ESTIMATED`
- rellena `estimated_liters`, `final_liters` y `final_source=AUTO`

Calculo automatico:

1. media historica confirmada de `net_liters`
2. media historica de `estimated_liters`
3. litros calculados por envase y numero
4. `60.00`

## 14. Ejecucion diaria

### 14.1 Iniciar jornada

Funcion:

- `start_route_day(route_day)`

Reglas:

- solo desde `PLANNED` o `PARTIAL`
- pasa a `IN_PROGRESS`
- setea `started_at` si no existia
- limpia `finished_at`

### 14.2 Registrar parada

Funcion:

- `complete_route_day_client(route_day, route_day_client, user, payload)`

Reglas:

- solo si `RouteDay.status == IN_PROGRESS`
- no permite registrar dos veces una parada
- por defecto exige orden secuencial
- permite saltar orden con `force=True`
- resuelve worker desde usuario, payload o ruta
- crea una `Collection`
- actualiza `CollectionRequest` si existe

La recogida se crea como:

- `PENDING_MEASUREMENT`, si se recoge
- `CANCELED`, si se marca cancelada

La medicion real se completa despues en nave.

### 14.3 Finalizar jornada

Funcion:

- `finish_route_day(route_day, close_action=None)`

Reglas:

- solo desde `IN_PROGRESS`
- si no hay paradas, queda `CANCELED` salvo accion explicita
- si quedan pendientes, exige `PARTIAL` o `CANCELED`
- si no quedan pendientes, queda `COMPLETED`

Conteo:

- `completed_stops`: paradas con alguna `Collection`
- `pending_stops`: total menos completadas

Punto de atencion:

- una parada con recogida cancelada cuenta como completada a efectos de cierre, porque ya fue gestionada.

## 15. Flujo frontend

### 15.1 `RouteForm`

Responsabilidad:

- crear o editar ruta
- cargar workers y zonas
- configurar `week_start` y `week_end`
- configurar zonas por dia
- guardar `zone-config` despues de crear o editar ruta

Punto importante:

- tras crear ruta, resuelve el id de respuesta para guardar zonas.

### 15.2 `RouteDetail`

Responsabilidad:

- cargar `operational-overview`
- mostrar resumen de ruta
- mostrar zonas por dia
- lanzar modal de generacion semanal
- iniciar/finalizar jornadas
- registrar paradas desde vista detalle
- abrir navegacion Google

Generacion:

- calcula semana sugerida segun `week_start`
- sugiere capacidad por camion o por jornadas ya existentes
- comprueba si hay paradas existentes en la semana
- solo muestra `regenerate` si hay paradas existentes
- envia `daily_capacity_liters`, `regenerate` y `auto_estimate_without_contact`

### 15.3 `GenerateWeekDialog`

Responsabilidad:

- pedir inicio de semana
- pedir capacidad diaria
- mostrar o esconder regeneracion
- permitir autoestimar sin contacto

Limitacion actual:

- no permite configurar capacidad distinta por dia
- no permite configurar `max_clients_per_day`

### 15.4 `RouteExecution`

Responsabilidad:

- operar una ruta en campo
- seleccionar semana
- seleccionar jornada
- mostrar mapa
- iniciar/finalizar jornada
- abrir Google Maps
- registrar parada

Usa:

- `operational_plan.active_segment_route_day_client_id` para sugerir la parada activa

### 15.5 `RouteDayMap`

Responsabilidad:

- pintar hub
- pintar paradas
- pintar lineas por segmentos
- mostrar estado visual de parada
- limitar seleccion de parada al segmento activo cuando aplica

Importante:

- el mapa usa lineas Leaflet entre puntos, no calcula carretera real
- la navegacion real se delega al endpoint de Google Maps

## 16. Flujo legacy eliminado

El flujo `generate-range-routes` se ha eliminado del backend.

Motivos:

- no estaba consumido por el frontend
- duplicaba responsabilidades de `generate-week`
- no creaba `CollectionRequest`
- no programaba autoestimaciones
- no aplicaba las mismas protecciones de mutabilidad
- tenia un comportamiento distinto ante fallos de Google

El unico flujo soportado para planificacion operativa queda centralizado en:

- `POST /routes/{id}/generate-week/`

## 17. Cobertura de tests observada

Backend cubre:

- creacion de ruta y respuesta con id
- generacion semanal con paradas y `CollectionRequest`
- autoestimacion sin contacto
- cierre bloqueado si quedan pendientes
- historico acotado a la misma empresa
- fallback de litros estimados
- default consistente de `max_clients_per_day`
- segmentacion por capacidad en `operational_plan`
- inclusion de `operational_plan` en overview
- URL de Google con retorno al hub entre segmentos
- URL de Google sin split, volviendo al hub al final
- orden base usando fecha efectiva entre ultima recogida y ultima planificacion
- optimizacion segmentada por capacidad
- optimizacion protegida ante paradas sin ubicacion
- division de navegacion Google en varios enlaces si hay demasiados waypoints

Frontend cubre:

- `GenerateWeekDialog` oculta o muestra regeneracion segun existan paradas

Huecos de tests recomendables:

- mock de Google Directions con respuesta valida y comprobacion de reordenacion
- mock de Google Directions fallando y comprobacion de fallback
- regeneracion bloqueada cuando hay `started_at`, `finished_at` o `Collection`
- capacidad por `days[]`
- cliente en borde de zona
- cliente sin ubicacion
- parada con ubicacion nula creada manualmente
- frontend enviando y mostrando `max_clients_per_day`, si se decide exponer

## 18. Riesgos y puntos de atencion

### 18.1 Google dentro de transaccion

La llamada a Google se ejecuta durante la generacion, dentro del flujo atomico.

Riesgo:

- locks de base de datos retenidos mientras se espera una API externa
- mayor latencia percibida en `generate-week`
- rollback completo si una excepcion no controlada aparece despues de crear paradas

Mejora:

- separar seleccion/creacion de paradas y optimizacion
- o lanzar optimizacion asincrona con Celery despues del commit
- o persistir primero el orden base y marcar la optimizacion como pendiente

### 18.2 Optimizacion por capacidad, no VRP completo

Estado actual:

- las paradas se agrupan por capacidad antes de llamar a Google
- Google optimiza cada segmento con salida y vuelta al hub
- si falla un segmento, se conserva su orden previo

Riesgo residual:

- no reparte demanda entre varios trabajadores
- no reubica automaticamente clientes omitidos por capacidad
- no considera ventanas horarias, turnos, tiempo de servicio ni trafico por hora

Esta limitacion es aceptable para una `v1` operativa, pero debe nombrarse como optimizacion de orden segmentada, no como optimizacion logistica integral.

### 18.3 Seleccion greedy de clientes

La seleccion de paradas recorre clientes ordenados por prioridad y los inserta si caben.

Riesgo:

- una combinacion distinta de clientes podria llenar mejor la capacidad diaria
- clientes grandes pueden quedar fuera aunque varios pequenos entren
- no existe redistribucion automatica entre dias de la semana

Mejora:

- registrar cuantos clientes quedaron fuera y por que motivo
- anadir una fase de rebalanceo entre dias habilitados
- evaluar un algoritmo de mochila simple antes de dar el salto a VRP completo

### 18.4 Litros previstos estimados

La capacidad depende de litros previstos, no de litros reales medidos en nave.

Riesgo:

- si las estimaciones son bajas, la ruta puede parecer viable y superar capacidad real
- si las estimaciones son altas, se pueden dejar clientes fuera innecesariamente

Mejora:

- mostrar confianza de estimacion
- priorizar historico confirmado reciente
- comparar litros previstos contra litros finalmente medidos para mejorar el estimador

### 18.5 Puntos en borde de poligono

El filtro moderno usa `location__within`.

Riesgo:

- clientes exactamente sobre el borde pueden quedar fuera

Mejora:

- revisar si conviene usar una geometria inclusiva o un pequeno buffer
- anadir test especifico para punto en borde de zona

### 18.6 Paradas sin ubicacion

La generacion automatica exige ubicacion, pero datos legacy o carga manual podrian producir paradas sin coordenadas.

Estado actual:

- `optimize_route_day_with_google` ignora esas paradas al llamar a Google
- conserva su posicion relativa al fusionar el resultado optimizado
- la navegacion externa solo incluye paradas ubicadas

Riesgo:

- el trabajador puede necesitar gestionar una parada que no aparece en Google Maps
- la segmentacion de navegacion puede diferir de la segmentacion operativa completa si faltan ubicaciones

Mejora:

- mostrar alerta de "paradas sin ubicacion" en detalle y ejecucion
- bloquear o revisar manualmente rutas con paradas no navegables

### 18.7 Limites practicos de Google

Hay dos limites distintos:

- Google Directions API durante la optimizacion
- URL de Google Maps durante la navegacion externa

Estado actual:

- la navegacion usa `GOOGLE_MAPS_NAVIGATION_MAX_WAYPOINTS = 8`
- si se supera el limite interno, el backend devuelve varios enlaces en `urls[]`
- el campo `url` se mantiene por compatibilidad con clientes antiguos

Riesgo:

- Google puede cambiar limites comerciales o tecnicos
- una jornada grande puede requerir varios enlaces y ser menos comoda en movil

Mejora:

- documentar limite visible en UI
- mostrar una lista ordenada de enlaces cuando `is_split=true`
- estudiar Google Routes API si se necesita una navegacion mas rica

### 18.8 Capacidad 0 equivale a sin limite

El serializer permite `0.00`.

Riesgo:

- un usuario puede creer que cero bloquea la generacion, pero en realidad desactiva el filtro

Mejora:

- aclararlo en UI
- o exigir capacidad minima mayor que cero si el negocio lo requiere

### 18.9 Parada individual mayor que capacidad

Si una parada supera por si sola la capacidad diaria, el plan la acepta en un segmento propio.

Riesgo:

- el plan puede representar una carga imposible para el camion asignado

Mejora:

- avisar al owner antes de generar
- permitir incluirla solo con confirmacion manual
- proponer cambio de camion o division manual de la recogida

### 18.10 Observabilidad limitada de la optimizacion

Actualmente el resultado de optimizacion se refleja en el orden final, pero no se persiste un objeto de auditoria.

Riesgo:

- cuesta explicar por que una ruta no se optimizo
- no hay metrica historica de fallos de Google, tiempo de respuesta o segmentos afectados

Mejora:

- guardar `optimization_status`, `optimization_reason` y `optimized_at` en `RouteDay`
- registrar numero de segmentos, paradas optimizadas y paradas excluidas por ubicacion

## 19. Alternativas de mejora evaluadas

### 19.1 Mantener Google Directions y endurecer la `v1`

Es la opcion mas conservadora.

Cambios:

- sacar Google de la transaccion principal
- persistir estado de optimizacion
- mostrar avisos de paradas sin ubicacion
- avisar de clientes omitidos por capacidad
- anadir tests de respuesta invalida y timeout de Google

Ventaja:

- bajo riesgo tecnico
- mantiene la arquitectura actual
- suficiente para una operativa con un trabajador por ruta y volumen moderado

Coste:

- no resuelve reparto multi-vehiculo ni ventanas horarias

### 19.2 Anadir heuristica local de fallback

Si Google no esta configurado o falla, se podria aplicar una heuristica local.

Opciones:

- vecino mas cercano desde el hub
- 2-opt sobre el orden resultante
- distancia euclidea/PostGIS como coste aproximado

Ventaja:

- mejora el orden incluso sin Google
- evita depender totalmente de una API externa

Coste:

- no calcula carreteras reales
- puede empeorar en zonas urbanas con rios, autovias o restricciones de giro

### 19.3 Usar matriz de distancias

En vez de pedir a Google un orden directo, se podria construir una matriz de tiempos/distancias.

Opciones:

- Google Distance Matrix API
- Google Routes API
- OSRM/GraphHopper si se quiere controlar infraestructura

Ventaja:

- permite algoritmos propios con coste mas realista
- base necesaria para VRP avanzado

Coste:

- mas llamadas o mayor coste por optimizacion
- mas cache y control de cuotas
- mas complejidad de implementacion

### 19.4 OR-Tools para VRP con restricciones

Opcion avanzada.

Permitiria modelar:

- capacidad por camion
- varios trabajadores/camiones
- retornos al hub
- ventanas horarias
- tiempo de servicio
- penalizacion por cliente no asignado
- maximo de jornada

Ventaja:

- solucion logistica mucho mas potente
- permite planificar a nivel empresa, no solo ruta individual

Coste:

- mayor complejidad tecnica
- requiere datos mas completos y fiables
- necesita UX para explicar soluciones, no solo generarlas

### 19.5 Persistir subviajes y descargas

Hoy los segmentos son calculados, no entidades.

Entidades posibles:

- `RouteTrip`
- `RouteSegment`
- `HubReturn`
- `UnloadEvent`

Ventaja:

- trazabilidad real de retornos a nave
- mejor analisis de operativa
- base para medir desviaciones entre plan y ejecucion

Coste:

- cambios de modelo, migraciones, endpoints y frontend
- mas estados que mantener correctamente

## 20. Recomendaciones priorizadas

### Prioridad alta

1. Sacar la llamada externa a Google fuera de la transaccion principal o hacerla asincrona.
2. Anadir tests de fallback de Google cuando devuelve error, timeout o estructura invalida.
3. Persistir o devolver metadata de optimizacion: aplicada, omitida, motivo y numero de segmentos.
4. Avisar en frontend cuando hay paradas sin ubicacion o paradas omitidas por capacidad.

### Prioridad media

1. Exponer `max_clients_per_day` en frontend si el owner necesita controlarlo.
2. Exponer capacidad por dia en frontend si hay dias con camiones o turnos diferentes.
3. Revisar filtro espacial en bordes de poligono.
4. Anadir UI dedicada para `is_split=true` en navegacion movil.
5. Detectar parada individual mayor que capacidad y exigir confirmacion.

### Prioridad baja

1. Crear heuristica local de fallback cuando Google no este disponible.
2. Cachear respuestas o matrices de distancia por coordenadas cercanas.
3. Persistir eventos reales de retorno a hub si la operativa lo necesita.
4. Evaluar OR-Tools solo cuando haya necesidad real de multi-vehiculo, ventanas horarias o optimizacion global.

## 21. Resumen ejecutivo

El flujo principal actual, `generate-week`, esta bien estructurado para el uso operativo:

- valida payload
- bloquea concurrencia
- respeta rango de ruta y dias operativos
- evita duplicados semanales
- filtra clientes por zona, empresa y frecuencia
- aplica capacidad y maximo de clientes
- optimiza con Google sin romper si falla
- crea solicitudes y automatiza autoestimacion
- preserva jornadas ya operadas

La parte mas solida es la trazabilidad:

- no se regenera una jornada ya iniciada o con recogidas
- las solicitudes se crean de forma idempotente
- los estados diarios protegen el flujo de ejecucion

La optimizacion actual es correcta como `v1` pragmatica:

- primero selecciona clientes de forma determinista
- despues segmenta por capacidad
- luego pide a Google un orden por cada segmento
- finalmente conserva fallback seguro si algo falla

La limitacion principal es que no es un VRP completo. Para el alcance actual esto esta bien, siempre que la documentacion y la UI lo llamen optimizacion de orden segmentada y no planificacion logistica global.

El mayor riesgo tecnico restante esta en que la llamada externa a Google sigue ocurriendo durante la generacion, por lo que puede mantener la transaccion abierta mas tiempo del ideal.

## 22. Diagrama de flujo simplificado

```text
Owner
  |
  v
POST /routes/{id}/generate-week/
  |
  v
GenerateWeekSerializer
  |
  v
generate_week_for_route
  |
  +--> lock cache + select_for_update
  |
  +--> validar rango de semana
  |
  +--> por cada dia de la semana
        |
        +--> comprobar rango y weekday
        |
        +--> crear/reutilizar RouteDay
        |
        +--> asignar capacidad
        |
        +--> generate_route_day_clients
              |
              +--> buscar RouteZoneDay
              |
              +--> filtrar clientes por empresa + zona + ubicacion
              |
              +--> calcular historico y frecuencia
              |
              +--> evitar duplicados semanales
              |
              +--> aplicar max_clients_per_day
              |
              +--> aplicar daily_capacity_liters
              |
              +--> crear RouteDayClient
              |
              +--> optimize_route_day_with_google
              |     |
              |     +--> dividir por capacidad
              |     |
              |     +--> optimizar cada segmento hub -> paradas -> hub
              |     |
              |     +--> conservar orden si Google falla
              |
              +--> crear/actualizar CollectionRequest
                    |
                    +--> notificar si procede
                    |
                    +--> programar autoestimacion si procede
```

## 23. Checklist de diagnostico rapido

Si una ruta no genera paradas, revisar:

- la semana esta dentro de `start_date` y `end_date`
- el weekday esta entre `week_start` y `week_end`
- existe `RouteZoneDay` para ese weekday
- las zonas tienen poligono
- los clientes tienen `location`
- los clientes pertenecen a la empresa
- los clientes estan dentro del poligono
- la frecuencia permite recogerlos en esa fecha
- no estan ya asignados en la misma semana
- la capacidad no los deja fuera
- no se alcanzo `max_clients_per_day`

Si una ruta no se optimiza, revisar:

- hay al menos 2 paradas con ubicacion
- existe `CompanyHub.location`
- existe `GOOGLE_MAPS_API_KEY`
- Google Directions responde con rutas
- los logs no muestran respuesta invalida de Google
- no hay una sola parada ubicada por segmento de capacidad

Si la navegacion no abre:

- hay paradas con ubicacion
- existe hub con ubicacion
- la URL devuelta existe
- el navegador o dispositivo permite abrir Google Maps
- si `is_split=true`, revisar todos los enlaces de `urls[]`

Si no llega solicitud al cliente:

- existe `CollectionRequest`
- `expires_at` no esta vencido
- Gmail esta configurado
- no esta activo el modo `auto_estimate_without_contact`
- no existe lock reciente de notificacion

Si la ruta queda con pocas paradas:

- revisar capacidad diaria
- revisar `max_clients_per_day`
- revisar frecuencia de clientes
- revisar si clientes ya quedaron asignados en otro dia de la misma semana
- revisar clientes sin ubicacion o fuera del poligono

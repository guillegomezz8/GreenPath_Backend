# Route Flow - Flujo de Rutas GreenPath

Fecha de revision: 2026-05-27

## 1. Objetivo del documento

Este documento describe el flujo completo del modulo de rutas en GreenPath, desde la configuracion de una ruta plantilla hasta la ejecucion diaria y su impacto en solicitudes, recogidas y navegacion.

Su objetivo es servir como referencia para:

- entender el comportamiento funcional del modulo de rutas
- localizar sus puntos de entrada en backend y frontend
- explicar que automatismos existen y bajo que condiciones
- documentar reglas de negocio y decisiones actuales del sistema

Tambien cumple una funcion especialmente importante dentro del TFG: explicar por que el modulo de rutas es el nucleo de complejidad funcional de GreenPath. En este flujo confluyen:

- el aislamiento multiempresa del dominio
- la geografia operativa basada en zonas y coordenadas reales
- la planificacion semanal con reglas de frecuencia
- la capacidad diaria de vehiculo
- la integracion con Google Maps
- la programacion asincrona con Celery y Redis
- la experiencia de uso movil para operativa de calle

Por tanto, este documento no debe leerse solo como una descripcion de endpoints, sino como la explicacion del motor logistico que diferencia GreenPath de una aplicacion administrativa convencional.

## 2. Stack tecnologico implicado en el flujo de rutas

El flujo de rutas no depende de una sola tecnologia, sino de varias piezas coordinadas.

### Backend

- Django
- Django REST Framework
- Django Filter
- PostgreSQL + PostGIS
- Celery
- Redis

### Frontend

- React
- Vite
- Tailwind CSS
- Leaflet / React Leaflet para mapa operativo

### Integraciones externas

- Google Maps Directions API para optimizacion del orden de paradas
- Google Maps / navegador del dispositivo para abrir navegacion externa
- Gmail API para correos asociados a `CollectionRequest` cuando procede

## 2.1 Por que este stack aporta valor real al proyecto

La complejidad del modulo de rutas no proviene solo del numero de tablas o endpoints, sino de la necesidad de coordinar tecnologias con responsabilidades muy distintas:

- `PostGIS` permite trabajar con geometria real y decidir que clientes pertenecen a una zona operativa
- `Google Maps Directions API` introduce optimizacion de orden y calculo de recorridos apoyados en un servicio externo
- `Leaflet / React Leaflet` trasladan esa planificacion a una interfaz visual comprensible, especialmente importante en movilidad
- `Celery` y `Redis` desacoplan del flujo sincrono tareas como autoestimaciones o notificaciones para no bloquear la operacion principal
- `Gmail API` aporta comunicacion automatizada con el cliente en torno a `CollectionRequest`

Esta combinacion es una de las razones por las que GreenPath se situa por encima de un CRUD academico tipico: el sistema tiene que orquestar reglas de negocio, datos geograficos, servicios de terceros y UX operativa en tiempo real.

## 3. Alcance del modulo de rutas

El modulo de rutas cubre estas responsabilidades:

- definir rutas plantilla
- asignar un trabajador a la ruta
- definir el rango de dias operativos de la semana
- asociar zonas por dia (`RouteZoneDay`)
- generar semanas operativas (`RouteDay` + `RouteDayClient`)
- optimizar el orden de paradas
- crear solicitudes previas de estimacion (`CollectionRequest`)
- permitir la ejecucion diaria de la jornada
- registrar paradas y crear recogidas reales

## 4. Entidades implicadas

### `Route`

Plantilla de ruta.
Contiene:

- empresa
- trabajador asignado
- fechas de vigencia
- inicio y fin de semana operativa

### `RouteZoneDay`

Relaciona una ruta con las zonas que debe cubrir en un weekday concreto.

### `RouteDay`

Jornada diaria generada para una fecha concreta.
Guarda estado, capacidad diaria y marcas reales de inicio/fin.

### `RouteDayClient`

Parada concreta dentro de un `RouteDay`.
Guarda cliente y orden planificado.

### `CollectionRequest`

Solicitud previa de envases y litros calculados asociada a una parada.

### `Collection`

Recogida real resultante de operar una parada.

## 5. Punto de entrada principal de planificacion

### Endpoint

- `POST /routes/{id}/generate-week/`
- `GET /routes/{id}/zone-config/`
- `PUT /routes/{id}/zone-config/`

### Backend

- View: `apps/route/api/viewsets/route_viewset.py` -> `generate_week`
- Serializer: `GenerateWeekSerializer`
- Configuracion de zonas: `RouteZoneConfigSerializer`
- Servicio principal: `apps/route/utils.py` -> `generate_week_for_route(...)`

### Permisos

- `generate-week` y `zone-config` solo puede ejecutarlos `owner`
- el detalle operativo y las acciones de ejecucion pueden usarlos el `owner` de la empresa o el `worker` asignado a la ruta

## 6. Flujo funcional de generacion semanal

Cuando el owner genera una semana, el flujo esperado es el siguiente:

1. selecciona ruta y fecha de inicio de semana
2. informa capacidad global o capacidades por dia
3. opcionalmente indica `regenerate`
4. backend valida permisos, rango de fechas y consistencia del payload
5. se crean o reutilizan `RouteDay`
6. se generan `RouteDayClient` por cada jornada valida
7. se optimiza el orden de paradas si procede
8. se crean o actualizan `CollectionRequest`
9. se programa autoestimacion con Celery
10. se devuelve resumen de jornadas generadas

## 7. Validaciones de entrada de `generate-week`

El endpoint soporta dos modos de capacidad:

### Modo A

- `daily_capacity_liters` global para todos los dias

### Modo B

- `days[]` con capacidad especifica por fecha

Reglas:

- `week_start_date` es obligatorio
- debe venir `daily_capacity_liters` o `days[]`
- no pueden venir ambos a la vez
- en `days[]` no puede haber fechas duplicadas
- las fechas de `days[]` deben estar dentro de la semana solicitada
- la semana debe estar dentro del rango de vigencia de la ruta
- `auto_estimate_without_contact` es opcional y por defecto vale `false`
- `max_clients_per_day` es opcional, tiene minimo `1`, maximo `100` y por defecto vale `10`
- el frontend actual envia `auto_estimate_without_contact`, pero no expone `max_clients_per_day`; en ese caso backend usa el limite por defecto

La configuracion de zonas por dia se guarda de forma separada mediante `zone-config`:

```json
{
  "zone_days": [
    {"weekday": 0, "zones": [1, 2]},
    {"weekday": 2, "zones": [3]}
  ]
}
```

`weekday` usa valores `0..6`, donde `0` es lunes y `6` es domingo.

## 8. Reglas clave de la generacion semanal

### 8.1 Idempotencia

La operacion es idempotente.
Si se repite una generacion sobre la misma semana, el backend reutiliza o actualiza jornadas segun el estado real del sistema.

### 8.2 `regenerate`

`regenerate=true` solo se permite si toda la semana sigue siendo editable.

Se bloquea cuando existen dias con:

- ejecucion previa
- recogidas asociadas
- trazabilidad operativa no reversible

### 8.3 Preservacion de jornadas ya operadas

Si `regenerate=false`, una jornada ya operada se preserva.
El sistema no altera sus paradas ni su capacidad.

### 8.4 Capacidad diaria

La capacidad diaria se aplica de forma estricta.
Si una nueva parada hace superar el total planificado del dia, no se inserta.

### 8.5 Limite maximo de clientes por dia

El backend respeta `max_clients_per_day` antes de seguir anadiendo clientes al `RouteDay`.

Criterio operativo actual:

- el valor funcional por defecto del sistema es `10` clientes por jornada
- ese limite se aplica junto con `daily_capacity_liters`
- si una jornada alcanza el tope de clientes aunque todavia quede capacidad, no se siguen insertando mas paradas en ese dia

Este criterio responde a una decision de negocio deliberada: no basta con llenar la jornada por litros; tambien hay que evitar dias artificialmente saturados en numero de paradas, porque eso penaliza tiempos de desplazamiento, carga cognitiva del conductor y calidad del servicio.

## 9. Seleccion de clientes para cada jornada

La generacion de paradas se hace en `generate_route_day_clients(...)`.

Pasos principales:

1. localizar las zonas del weekday actual (`RouteZoneDay`)
2. buscar clientes con geolocalizacion dentro de esas zonas
3. restringir por empresa de la ruta
4. calcular historico previo del cliente dentro de la misma empresa
5. aplicar frecuencia de recogida
6. evitar duplicidades de un mismo cliente en la misma semana
7. insertar paradas respetando capacidad y limite diario

## 10. Reglas de frecuencia de cliente

Se usan las frecuencias configuradas en cliente:

- `WEEKLY` -> 7 dias
- `2_WEEKS` -> 14 dias
- `3_WEEKS` -> 21 dias
- `4_WEEKS` -> 28 dias

La decision de si un cliente esta "due" se apoya en:

- ultima recogida real
- ultima planificacion previa
- ambas calculadas dentro de la misma empresa de la ruta

Esto evita mezclar historico si un cliente pertenece a mas de una empresa.

En terminos funcionales, esta regla es clave para el enfoque multiempresa del TFG: un mismo cliente puede existir vinculado a varias empresas, pero la generacion de una semana debe respetar exclusivamente el contexto operativo e historico de la empresa que esta planificando la ruta.

## 11. Optimizacion con Google Directions

### Funcion principal

- `apps/route/utils.py` -> `optimize_route_day_with_google(route_day, planned_liters_by_row=None)`

### Comportamiento

1. toma clientes del dia en orden actual
2. calcula segmentos segun capacidad diaria y litros previstos
3. usa `CompanyHub.location` como origen y destino de cada segmento
4. envia a Google las paradas ubicadas con `waypoints=optimize:true|...`
5. conserva las paradas sin ubicacion en su posicion relativa
6. reescribe `RouteDayClient.order` si la respuesta es valida

### Cuando no se aplica

La optimizacion no se aplica si:

- hay menos de 2 paradas
- hay menos de 2 paradas con ubicacion
- la empresa no tiene hub
- no existe `GOOGLE_MAPS_API_KEY`
- Google responde error o estructura invalida

### Fallback

En todos esos casos se conserva el orden existente y el flujo no se rompe.

### Alcance real de la optimizacion

La optimizacion actual es una optimizacion de orden segmentada.

Si la capacidad diaria obliga a volver al hub, el backend no manda todo el dia como una unica secuencia: divide la jornada en segmentos y optimiza cada segmento como:

```text
hub -> paradas del segmento -> hub
```

No es todavia un VRP completo. No decide automaticamente reparto entre varios trabajadores, ventanas horarias, turnos, tiempo de servicio ni reasignacion de clientes omitidos por capacidad.

Eso no reduce el valor del modulo; al contrario, refleja una decision tecnica sensata para un TFG con foco realista. Se implementa una optimizacion util y defendible para el negocio actual, sin sobredisenar un solucionador de rutas global cuando el modelo operativo vigente trabaja con una ruta y un trabajador asignado.

## 12. Capacidad, litros previstos y tramos operativos

La version actual del sistema incorpora una `v1` de control operativo por capacidad diaria sin introducir nuevas entidades persistentes para subviajes o descargas intermedias.

### Principio funcional

Una jornada (`RouteDay`) sigue siendo una unica unidad operativa, pero internamente puede dividirse en varios `tramos operativos` si la suma de litros previstos obliga a volver al hub antes de continuar.

Es importante entender que `tramo` no se trata aqui como una entidad de negocio visible para el usuario final, sino como una abstraccion tecnica interna que permite:

- mantener una sola jornada diaria coherente en base de datos
- calcular cuando la capacidad obliga a volver a nave
- sincronizar optimizacion, mapa y navegacion externa
- simplificar la interfaz para que el trabajador vea decisiones operativas y no estructuras internas complejas

### Datos usados para calcular la carga prevista de una parada

El backend resuelve la carga prevista de cada parada siguiendo este orden:

1. `CollectionRequest.final_liters` si existe
2. `CollectionRequest.estimated_liters` si existe
3. calculo por envases (`container_type` + `container_number`)
4. `0.00` si no hay informacion suficiente

### Regla de corte por capacidad

Si al anadir la siguiente parada la carga prevista acumulada supera `RouteDay.daily_capacity_liters`, el sistema:

- cierra el tramo actual
- inserta una vuelta implicita al hub
- abre un nuevo tramo para continuar con las paradas restantes

### Consecuencia funcional

Esto permite reflejar internamente:

- cuantos bloques reales de trabajo tiene el dia
- cuantas veces se volveria a nave
- que parada deberia proponerse como siguiente
- cuando la navegacion debe insertar retornos intermedios al hub

### Alcance de esta `v1`

Esta `v1`:

- representa el retorno al hub a nivel de plan operativo y navegacion
- expone esa informacion al frontend
- no crea todavia entidades persistentes del tipo `RouteTrip`, `Unload` o `ReturnToHub`
- no registra eventos reales de descarga en base de datos

Esta aproximacion tiene mucho valor para el TFG porque demuestra capacidad de modelado incremental: se resuelve un problema logistico real con una capa intermedia de plan operativo, sin introducir prematuramente nuevas tablas o un dominio excesivamente rigido.

## 13. CollectionRequest y automatizacion asociada

Cada parada generada puede crear o actualizar una `CollectionRequest`.

### Regla temporal

- `expires_at = inicio_route_day - 36 horas`

### Programacion

- si `expires_at` ya vencio, la tarea se ejecuta inmediatamente
- si no ha vencido, se agenda con `eta=expires_at`

### Dedupe

Si una solicitud ya tenia una task programada y se recalcula, la task anterior se revoca y se reprograma.

### Notificacion

Cuando la solicitud es nueva, se puede lanzar notificacion por email al cliente.

## 14. Flujo de respuesta del cliente

El cliente puede interactuar con su solicitud mediante:

- `GET /collections/requests/me/`
- `GET /collections/requests/{id}/`
- `POST /collections/requests/{id}/answer/`

Owner o worker pueden resolver una solicitud manualmente mediante:

- `POST /collections/requests/{id}/manual/`

El sistema admite estos estados:

- `PENDING`
- `AUTO_ESTIMATED`
- `ANSWERED`
- `MANUAL`

Reglas:

- el cliente solo responde mientras la solicitud no este expirada
- owner o worker pueden fijar litros manualmente
- si no hay respuesta a tiempo, Celery puede autoestimar

## 15. Ejecucion operativa de una jornada

Una vez generada la semana, la operacion diaria se concentra en estos endpoints:

- `POST /routes/{id}/route-days/{route_day_id}/start/`
- `POST /routes/{id}/route-days/{route_day_id}/finish/`
- `POST /routes/{id}/route-days/{route_day_id}/stops/{route_day_client_id}/complete/`
- `GET /routes/{id}/route-days/{route_day_id}/google-navigation/`
- `GET /routes/{id}/operational-overview/`

### Datos operativos que consume el frontend

El `operational-overview` devuelve ahora, ademas del listado de paradas, un bloque `operational_plan` por cada `RouteDay`.

Ese bloque incluye, entre otros, los siguientes datos:

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
- `segments[]`

### Uso funcional en frontend

La pantalla `RouteExecution` utiliza este bloque para:

- proponer por defecto la siguiente parada pendiente correcta
- construir el recorrido del dia en mapa
- exportar una navegacion coherente con retornos al hub cuando la capacidad lo exige
- simplificar la UX operativa sin exponer al usuario tarjetas tecnicas de `tramo`, `segmento` o metrica interna innecesaria

La idea de producto actual es clara: la complejidad de segmentacion debe existir en backend y en la logica de apoyo, pero la experiencia de usuario debe expresarla como decisiones simples del tipo "siguiente parada", "debes volver a nave" o "ya puedes continuar".

## 16. Reglas de `start`, `complete` y `finish`

### `start`

- solo desde estados permitidos (`PLANNED` o `PARTIAL`)
- cambia a `IN_PROGRESS`
- fija `started_at`

### `complete`

- solo con `RouteDay` en `IN_PROGRESS`
- por defecto no permite saltarse el orden
- admite `force=true` cuando el flujo lo requiere
- crea o actualiza `Collection`
- actualiza la solicitud asociada cuando procede
- usa precio global de empresa por defecto si existe

#### Importante en la `v1` de tramos

La parada registrada:

- si esta cancelada, cuenta como gestionada pero no suma carga operativa del tramo
- si queda registrada como recogida, suma su carga prevista al tramo correspondiente

La medicion final no se usa para operar la ruta en calle, porque esa fase pertenece al trabajo posterior en nave.

### `finish`

- solo desde `IN_PROGRESS`
- si no quedan pendientes: `COMPLETED`
- si quedan pendientes: exige decision entre `PARTIAL` o `CANCELED`
- una parada cancelada cuenta como procesada y no impide cerrar como `COMPLETED` si no quedan pendientes reales

## 17. Exportacion de navegacion y retorno al hub

El endpoint `google-navigation` ya no exporta una simple secuencia lineal de clientes.

Ahora construye la URL a partir del mismo `operational_plan` usado por el frontend, de forma que:

- el origen es el hub
- el destino es el hub
- entre tramos se inserta el hub como waypoint intermedio

Consecuencia:

- si el dia cabe en una sola carga, se exporta una sola secuencia
- si el dia requiere varios tramos, Google recibe un recorrido con retornos intermedios a nave
- si hay demasiados waypoints, se devuelven varios enlaces en `urls[]` y `is_split=true`
- en el caso dividido, cada enlace empieza y termina en el hub para mantener una navegacion manejable

Esto mantiene alineados:

- planificacion
- ejecucion visual
- navegacion externa

## 18. Relacion con `Collection`

Al operar una parada, el sistema crea o actualiza la recogida real.

Puntos importantes:

- la recogida puede nacer pendiente de medicion
- la medicion final se consolida despues en nave
- si no se informa `price_per_liter`, se toma por defecto desde `CompanySettings`
- la recogida puede marcarse como `billable` o no

### Impacto economico

Solo las recogidas:

- `CONFIRMED`
- `billable=true`

computan en los costes y en el resumen economico global.

## 19. Frontend asociado al flujo de rutas

### `RouteDetail`

Ruta:

- `/routes/:id`

Responsabilidad:

- planificacion semanal
- consulta de estados por jornada
- acceso a generacion semanal
- acceso a la operativa diaria

### `RouteExecution`

Ruta:

- `/routes/:id/execute`

Responsabilidad:

- ejecutar la jornada diaria
- mostrar mapa operativo
- iniciar/finalizar jornada
- seleccionar parada activa
- registrar recogida
- fijar por defecto la semana operativa actual de la ruta

La separacion entre `RouteDetail` y `RouteExecution` es una decision importante del proyecto: evita sobrecargar una sola pantalla con planificacion, analitica, tabla de dias, mapa y operacion de calle. De este modo, la parte administrativa y la parte operativa conviven, pero sin competir visualmente entre si.

### Componentes clave

- `GenerateWeekDialog`
- `RouteDayMap`
- `RouteActionButton`

## 20. Responsive y UX del modulo de rutas

El modulo de rutas es uno de los mas sensibles en movilidad, por eso se han tomado varias decisiones especificas:

- separacion entre detalle y ejecucion
- mapa y panel operativo adaptados por breakpoint
- modales de registro y cierre con scroll interno
- acciones primarias a ancho completo en movil
- contadores plegables en listados
- chips o selectores compactos para jornadas y estados
- simplificacion deliberada de la pantalla operativa para no mostrar tecnicismos internos de segmentacion

## 21. Filtros principales del modulo

### Filtro de rutas

`RouteFilter` soporta:

- `date`
- `status`
- `search`

Busqueda sobre:

- `name`
- `company__name`
- `worker__name`
- `worker__surname`

### Vista operativa

La vista `operational-overview` admite `week_start_date=YYYY-MM-DD` para cargar una semana concreta.

## 22. Riesgos y puntos de atencion

- clientes sin geolocalizacion no entran en planificacion automatica
- zonas mal definidas reducen calidad de la generacion
- sin hub o sin Google API key no hay optimizacion real del orden
- regenerar semanas ya operadas esta bloqueado para proteger trazabilidad
- la capacidad diaria debe entenderse como restriccion operativa, no como simple campo informativo
- capacidad `0.00` equivale a sin limite de capacidad
- una parada individual mayor que la capacidad queda en un segmento propio y deberia revisarse manualmente
- la seleccion de clientes es greedy; no resuelve una combinacion global optima de todos los clientes
- Google se consulta durante la generacion, por lo que conviene vigilar latencia y fallos externos
- la navegacion externa solo incluye paradas con ubicacion

## 23. Valor tecnico del modulo dentro del TFG

El flujo de rutas es probablemente el mejor ejemplo de la complejidad real de GreenPath, porque obliga a integrar:

- reglas de negocio sobre frecuencia de cliente y estado de solicitudes
- logica relacional entre `Route`, `RouteDay`, `RouteDayClient`, `CollectionRequest` y `Collection`
- datos geoespaciales soportados por PostGIS
- consumo de Google Maps para optimizar y exportar recorridos
- procesos asincronos en Celery con soporte de Redis
- una interfaz responsive y util en movilidad

Esto permite defender academicamente que el proyecto no se limita a almacenar informacion, sino que implementa un flujo logistico real con dependencias tecnicas heterogeneas y decisiones de arquitectura justificadas.

## 24. Resumen ejecutivo del flujo

- el owner configura ruta, zonas y capacidades
- el sistema genera jornadas y paradas
- Google puede optimizar el orden
- se crean solicitudes al cliente con expiracion automatica
- owner o worker ejecutan la jornada diaria
- la navegacion diaria siempre parte del hub y termina en el hub; si la capacidad obliga, inserta retornos intermedios a nave
- cada parada puede terminar en recogida real
- la recogida medida y facturable impacta en estadisticas economicas

## 25. Observabilidad y control operativo del flujo

Para diagnosticar incidencias en rutas conviene revisar:

- logs de backend durante `generate-week`
- logs de Google cuando la optimizacion no se aplica
- tareas Celery asociadas a `CollectionRequest`
- estado real de `RouteDay`, `RouteDayClient` y `Collection`

Senales utiles de comprobacion:

- numero de jornadas generadas
- numero de paradas insertadas
- existencia de solicitudes programadas
- estado final correcto de la jornada tras `finish`

## 26. Checklist de validacion manual del modulo

Una validacion funcional minima del flujo de rutas deberia cubrir:

- crear o editar una ruta plantilla
- definir zonas por dia
- generar una semana dentro de rango
- comprobar que se crean jornadas y solicitudes
- iniciar una jornada desde `RouteExecution`
- registrar una parada
- finalizar sin pendientes
- finalizar con pendientes obligando a decidir
- revisar que una parada cancelada no bloquee un cierre completo si ya no quedan pendientes reales

## 27. Evolucion prevista del modulo

Las lineas de evolucion mas razonables del modulo de rutas son:

- sacar la optimizacion de Google fuera de la transaccion principal o ejecutarla de forma asincrona
- persistir metadata de optimizacion: aplicada, omitida, motivo, segmentos y fecha
- mostrar en UI clientes omitidos por capacidad y paradas sin ubicacion
- exponer `max_clients_per_day` y capacidad por dia si el owner necesita control fino
- anadir fallback local con heuristica simple cuando Google no este disponible
- estudiar matrices de distancia o Google Routes API si se necesita mas precision
- evaluar OR-Tools solo si aparece necesidad real de multi-vehiculo, ventanas horarias o optimizacion global
- persistir subviajes, retornos a hub o descargas reales si la operativa necesita trazabilidad avanzada
- pruebas end-to-end centradas en operacion movil y navegacion dividida

## 28. Referencias relacionadas

- `docs/FUNCIONAL.md`
- `docs/API.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/DESPLIEGUE_Y_OPERACION.md`

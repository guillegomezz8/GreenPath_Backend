# Integraciones y APIs Externas GreenPath

Fecha de revision: 2026-05-27

## 1. Objetivo del documento

Este documento recoge de forma especifica las APIs, servicios externos y librerias de terceros con impacto funcional relevante utilizados por GreenPath, el papel que cumple cada integracion dentro del sistema y las decisiones tecnicas asociadas a su uso.

Su objetivo es cubrir una parte importante de la memoria del TFG que a menudo queda dispersa entre documentos tecnicos: que servicios externos se usan, para que se usan, como se configuran, que complejidad introducen y que ocurre cuando no estan disponibles.

## 2. Mapa general de integraciones

| Integracion | Tipo | Uso principal | Modulos implicados | Criticidad |
| --- | --- | --- | --- | --- |
| Google Maps Platform | API externa | Geocodificacion y optimizacion de rutas | `user`, `route`, frontend de rutas | Media |
| Google Identity Services | API externa | Login social con Google ID token | frontend `SocialLogin`, backend `auth` | Media |
| Gmail API | API externa | Envio de correos operativos y de acceso | `base`, `collection`, `user` | Media |
| WeasyPrint | Libreria de terceros | Generacion de facturas PDF | `sale` | Alta dentro del bloque de ventas |
| Celery | Infraestructura de procesos | Tareas asincronas y automatizacion | `collection`, `base`, `route` | Alta en flujos diferidos |
| Redis | Servicio auxiliar | Broker y backend de resultados | infraestructura | Alta cuando hay tareas diferidas |
| Leaflet / React Leaflet | Libreria frontend | Visualizacion cartografica | `routes`, `zones`, `settings` | Media |

## 2.1 Valor academico y tecnico de estas integraciones

La complejidad de GreenPath no viene solo del numero de entidades o pantallas. Una parte importante del valor del TFG aparece al integrar librerias y APIs especializadas en puntos criticos del flujo:

- geocodificacion de clientes
- optimizacion logistica
- navegacion real en campo
- envio de correos operativos
- generacion documental de facturas
- ejecucion asincrona de tareas que no deben bloquear la experiencia del usuario

Esto obliga a resolver configuracion por entorno, manejo de secretos, dependencias del sistema, comportamiento degradado cuando un tercero falla y coherencia entre backend, frontend y tareas auxiliares.

## 3. API propia del proyecto

Aunque este documento se centra en integraciones externas, conviene dejar claro que GreenPath expone tambien una API propia REST construida con Django REST Framework.

Esta API interna del proyecto:

- sirve de contrato entre backend y frontend
- concentra la logica de autorizacion, validacion y reglas de negocio
- se documenta en `docs/API.md`
- puede inspeccionarse mediante:
  - `http://localhost:8000/docs/`
  - `http://localhost:8000/schema/`

Los principales dominios expuestos por esa API son:

- autenticacion
- usuarios, clientes y trabajadores
- empresa y configuracion
- zonas y camiones
- rutas y operacion diaria
- recogidas y solicitudes
- compradores y ventas

## 4. Google Maps Platform

### 4.1 Objetivo funcional

Google Maps Platform se utiliza para resolver tres necesidades distintas:

- geocodificar direcciones de clientes
- optimizar provisionalmente el orden de paradas en la generacion semanal
- abrir navegacion externa desde la interfaz operativa

### 4.2 Uso real dentro del sistema

#### Geocodificacion de clientes

Cuando se crea o edita un cliente, el sistema puede construir una direccion completa a partir de:

- direccion
- ciudad
- codigo postal
- pais

Con esa informacion se consulta la API de geocodificacion para obtener coordenadas y almacenarlas en `Client.location`.

Impacto funcional:

- permite incluir al cliente en filtros geograficos
- facilita su visualizacion en mapas
- hace posible la seleccion por zonas

#### Optimizacion de rutas

Durante `generate-week`, una vez seleccionados los clientes validos para un `RouteDay`, el sistema puede llamar a Google Directions para obtener un orden de paradas optimizado con `optimize:true`.

Impacto funcional:

- mejora el orden operativo inicial
- reduce trabajo manual posterior
- mantiene un fallback funcional si Google no esta disponible

#### Navegacion operativa

Desde la pantalla `RouteExecution`, el usuario puede abrir un enlace de navegacion externa basado en las coordenadas del hub y de las paradas. En movil se intenta favorecer la apertura de la app de Google Maps si esta instalada.

En la version actual, esta navegacion ya no se exporta como una simple cadena lineal de clientes. La URL se construye a partir del `operational_plan` del dia, por lo que:

- origen = hub
- destino = hub
- si la capacidad prevista obliga a dividir la jornada, el hub aparece tambien entre segmentos como waypoint intermedio

Esto permite que Google Maps refleje mejor el recorrido real esperado de una jornada con varias cargas o varios retornos operativos a nave.

### 4.3 Configuracion necesaria

Variables de entorno implicadas:

- `GOOGLE_MAPS_API_KEY`

Para que la integracion sea util, la clave debe tener habilitados los servicios correspondientes del proyecto de Google Cloud.

### 4.4 Comportamiento cuando falla o no esta disponible

El sistema se ha disenado para no depender de Google como condicion indispensable del flujo base.

Si la clave no existe o la llamada falla:

- la geocodificacion no se completa automaticamente
- la optimizacion de paradas se omite
- el backend deja trazabilidad por logging
- la aplicacion sigue pudiendo funcionar con orden secuencial o datos ya guardados

Esto es importante porque evita que una integracion opcional tumbe el flujo principal del negocio.

### 4.5 Riesgos y consideraciones

- coste variable segun uso y cuotas del proveedor
- necesidad de custodiar correctamente la API key
- dependencia de la calidad de la direccion aportada
- comportamiento desigual si algunos clientes no tienen coordenadas validas

## 4.6 Google Identity Services para login social

El frontend carga el cliente de Google Sign-In desde `https://accounts.google.com/gsi/client` y obtiene un Google ID token. Despues llama al backend con:

- endpoint: `POST /authenticate/login`
- campo principal usado por el frontend: `token`
- compatibilidad backend: tambien acepta `credential`

El backend valida el token contra los client ids configurados y solo permite el acceso si existe un usuario GreenPath con el email verificado recibido desde Google.

Variables implicadas:

- backend: `GOOGLE_CLIENT_ID`
- frontend: `VITE_GOOGLE_CLIENT_ID`
- frontend opcional: `VITE_GOOGLE_SIGNATURE`

Este flujo convive con el login por credenciales (`POST /login/`) y usa los mismos tokens JWT de sesion una vez autenticado el usuario.

## 5. Gmail API

### 5.1 Objetivo funcional

Gmail API se utiliza para el envio de correos salientes desde la plataforma. Su uso actual cubre principalmente:

- envio de correos de acceso a usuarios nuevos
- envio de notificaciones de `CollectionRequest`

### 5.2 Uso real dentro del sistema

#### Correo de acceso

Cuando se crea un usuario desde los flujos de cliente o trabajador, el sistema puede enviar un correo con informacion de acceso, reutilizando una plantilla HTML comun con la estetica del proyecto.

#### Notificacion de solicitud al cliente

Cuando se crea una `CollectionRequest`, el sistema puede notificar al cliente que tiene una solicitud pendiente de respuesta. Este flujo se ejecuta de forma asincrona para no bloquear la operacion principal.

### 5.3 Configuracion necesaria

Variables de entorno implicadas:

- `GMAIL_FROM`
- `GMAIL_CLIENT_SECRET_JSON`
- `GMAIL_TOKEN_JSON`

Estas variables deben configurarse correctamente para que la integracion funcione. En particular:

- los JSON deben ir en una sola linea dentro de `.env`
- el token OAuth debe ser valido y renovable
- el emisor no debe llevar espacios residuales

### 5.4 Comportamiento cuando falla o no esta disponible

La aplicacion tolera la ausencia de Gmail API en los flujos operativos.

Si la integracion no esta lista:

- se omite el envio del correo
- se registra un warning por logging
- el flujo funcional principal no se detiene

Esta decision es importante porque el negocio no debe dejar de operar por una incidencia en el canal de correo.

### 5.5 Riesgos y consideraciones

- caducidad o revocacion de credenciales OAuth
- configuracion sensible en `.env`
- dependencia de una cuenta de Google correctamente autorizada
- necesidad de controlar bien secretos y tokens en entornos de entrega

## 6. WeasyPrint y generacion PDF

### 6.1 Por que aparece en este documento

WeasyPrint no es una API externa en sentido estricto, pero si es una integracion de terceros relevante para el proyecto y para la memoria tecnica, porque soporta una funcionalidad con impacto directo en negocio: la emision de facturas PDF.

### 6.2 Uso dentro del sistema

El modulo `sale` utiliza WeasyPrint para:

- renderizar facturas desde HTML y CSS
- componer el documento cada vez que se descarga una factura
- exponer descarga del PDF asociado sin persistir el binario

### 6.3 Ventaja tecnica de esta eleccion

La eleccion de WeasyPrint frente a soluciones mas de bajo nivel permite:

- trabajar con plantillas HTML mantenibles
- controlar mejor la maquetacion visual
- acercar la salida PDF al aspecto de una factura real

### 6.4 Dependencias del entorno

La integracion requiere dependencias del sistema dentro de la imagen Docker. Por ello, no basta con instalar el paquete Python: el contenedor debe incluir tambien las librerias necesarias para el renderizado.

### 6.5 Decision actual sobre persistencia documental

En la version actual del proyecto, el PDF de factura:

- no se almacena como fichero persistido
- se genera al vuelo en cada descarga
- se construye con la venta, sus lineas y el snapshot fiscal del emisor asociado

Esta decision reduce almacenamiento innecesario y asegura que el documento final conserve los datos fiscales y bancarios historicos del emisor aunque cambie la configuracion global.

## 7. Estrategia general ante integraciones externas

GreenPath sigue una serie de principios comunes para el uso de APIs y servicios externos:

- el flujo principal del negocio no debe depender de un tercero cuando no sea imprescindible
- las credenciales deben mantenerse fuera de codigo
- los fallos deben dejar rastro en logs
- el frontend no debe asumir que una integracion siempre existe
- la documentacion debe explicar claramente que integra, como y con que limites
- cuando sea posible, el sistema debe degradar a un modo util en lugar de bloquear el flujo principal

## 7.1 Celery y Redis como infraestructura de integracion interna

Aunque Celery y Redis no son APIs de negocio externas en el mismo sentido que Google Maps o Gmail API, forman parte de la complejidad integradora real del proyecto y por eso conviene tratarlos aqui.

### Papel de Celery

Celery permite sacar del flujo sincrono de peticion-respuesta varias tareas que no deben bloquear al usuario:

- autoestimacion de `CollectionRequest` cuando expira
- notificaciones por correo
- tareas programadas o reprocesos asociados a cambios de planificacion

Sin esta capa, determinadas operaciones quedarían demasiado acopladas al tiempo de respuesta de la API y a la disponibilidad inmediata de terceros como Gmail.

### Papel de Redis

Redis actua como:

- broker de mensajes
- backend de resultados
- soporte de coordinacion para workers Celery

Su uso aporta una separacion clara entre:

- logica de negocio principal
- ejecucion diferida
- observabilidad del estado de tareas

### Valor tecnico

Desde la perspectiva del TFG, la presencia de Celery y Redis demuestra que GreenPath no se limita a un flujo web elemental. El proyecto incorpora procesos asincronos reales, planificacion diferida y tolerancia a trabajos lentos o no inmediatos.

## 7.2 Leaflet y React Leaflet en la experiencia operativa

Leaflet y React Leaflet permiten integrar la capa geografica directamente dentro de la interfaz del producto.

Su uso actual cubre:

- representacion de zonas sobre mapa
- visualizacion del hub de empresa
- visualizacion de clientes y paradas
- apoyo visual a la ejecucion diaria de rutas

Valor añadido:

- evita depender por completo de vistas embebidas de terceros
- permite personalizar la experiencia de mapa segun el dominio operativo
- refuerza el valor del proyecto en su parte logistica y geoespacial

## 8. Variables de entorno relacionadas

Resumen de variables clave:

| Variable | Uso |
| --- | --- |
| `GOOGLE_MAPS_API_KEY` | Geocodificacion y optimizacion con Google |
| `GOOGLE_CLIENT_ID` | Validacion backend de Google ID tokens para login social |
| `GMAIL_FROM` | Remitente de los correos |
| `GMAIL_CLIENT_SECRET_JSON` | Cliente OAuth de Gmail API |
| `GMAIL_TOKEN_JSON` | Token OAuth para envio real |

Variables del frontend:

| Variable | Uso |
| --- | --- |
| `VITE_APP_API_URL` | URL base de la API backend consumida por Axios |
| `VITE_GOOGLE_CLIENT_ID` | Client id web usado por Google Sign-In |
| `VITE_GOOGLE_SIGNATURE` | Metadato/firma enviado por `SocialLogin` cuando esta configurado |

Variables relacionadas de infraestructura asíncrona:

| Variable | Uso |
| --- | --- |
| `CELERY_BROKER_URL` | Conexion del broker de Celery |
| `CELERY_RESULT_BACKEND` | Backend de resultados de Celery |

## 9. Impacto academico de estas integraciones

Desde la perspectiva del TFG, estas integraciones aportan valor porque demuestran:

- capacidad de integrar servicios externos reales
- criterio para decidir que partes del sistema deben tolerar fallos externos
- manejo de configuracion sensible
- coordinacion entre backend, frontend y procesos asincronos
- generacion documental con calidad suficiente para un caso de uso real
- uso de infraestructura auxiliar mas alla de una base de datos y una API CRUD

## 10. Coste, cuotas y control operativo

Desde el punto de vista de proyecto, las integraciones no son solo una cuestion tecnica, sino tambien operativa.

### 10.1 Google Maps Platform

Aspectos a vigilar:

- consumo de cuota
- coste asociado al uso de Directions y Geocoding
- restriccion de la API key por entorno o dominio

### 10.2 Gmail API

Aspectos a vigilar:

- validez del token OAuth
- revocacion manual de credenciales
- dependencia de la cuenta emisora

### 10.3 WeasyPrint

Aspectos a vigilar:

- presencia de dependencias del sistema en la imagen Docker
- consistencia de la plantilla HTML/CSS
- correcta generacion bajo demanda del PDF

### 10.4 Celery y Redis

Aspectos a vigilar:

- disponibilidad del broker
- correcta ejecucion de workers
- sincronizacion con Celery Beat cuando existen tareas programadas
- visibilidad del estado de las tareas en desarrollo, pruebas y demo

## 11. Seguridad de integraciones y custodia de secretos

Las integraciones utilizadas por GreenPath implican custodiar informacion sensible.
Por ello se recomienda:

- no versionar secretos ni tokens en el repositorio
- utilizar `.env` o mecanismos equivalentes por entorno
- rotar credenciales expuestas o sospechosas
- restringir el acceso a claves de Google
- conservar copia segura y privada del cliente OAuth de Gmail

## 12. Criterios de eleccion de integraciones

Las integraciones elegidas responden a criterios concretos:

- Google Maps aporta geocodificacion y optimizacion realista para un caso de uso logistico
- Google Identity Services permite integrar login social sin sustituir el modelo propio de usuarios y roles
- Gmail API permite un canal formal de notificacion sin depender de envio local improvisado
- WeasyPrint permite facturas PDF mantenibles a partir de HTML y CSS versionables
- Celery y Redis permiten desacoplar expiraciones y notificaciones del tiempo de respuesta normal
- Leaflet permite integrar el mapa dentro de la aplicacion sin delegar toda la experiencia cartografica a un servicio externo

Ademas, estas elecciones tienen sentido en conjunto: cada pieza cubre una dimension distinta del problema real del negocio, y juntas construyen un sistema mas rico que una aplicacion de gestion administrativa convencional.

Estas elecciones se consideran razonables para un TFG porque aportan valor funcional visible sin exigir una infraestructura desproporcionada.

## 13. Documentos relacionados

Para ampliar esta informacion conviene consultar tambien:

- `docs/API.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/ROUTE_FLOW.md`
- `docs/MEMORIA_FUNCIONAL_TFG.md`
- `docs/DESPLIEGUE_Y_OPERACION.md`
- `docs/BIBLIOGRAFIA_Y_FUENTES.md`

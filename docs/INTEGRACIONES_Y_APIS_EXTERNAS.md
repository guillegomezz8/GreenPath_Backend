# Integraciones y APIs Externas GreenPath

Fecha de revision: 2026-04-14

## 1. Objetivo del documento

Este documento recoge de forma especifica las APIs y servicios externos utilizados por GreenPath, el papel que cumple cada integracion dentro del sistema y las decisiones tecnicas asociadas a su uso.

Su objetivo es cubrir una parte importante de la memoria del TFG que a menudo queda dispersa entre documentos tecnicos: que servicios externos se usan, para que se usan, como se configuran y que ocurre cuando no estan disponibles.

## 2. Mapa general de integraciones

| Integracion | Tipo | Uso principal | Modulos implicados | Criticidad |
| --- | --- | --- | --- | --- |
| Google Maps Platform | API externa | Geocodificacion y optimizacion de rutas | `user`, `route`, frontend de rutas | Media |
| Gmail API | API externa | Envio de correos operativos y de acceso | `base`, `collection`, `user` | Media |
| WeasyPrint | Libreria de terceros | Generacion de facturas PDF | `sale` | Alta dentro del bloque de ventas |

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
- regenerar el documento cuando se actualiza una venta
- exponer descarga del PDF asociado

### 6.3 Ventaja tecnica de esta eleccion

La eleccion de WeasyPrint frente a soluciones mas de bajo nivel permite:

- trabajar con plantillas HTML mantenibles
- controlar mejor la maquetacion visual
- acercar la salida PDF al aspecto de una factura real

### 6.4 Dependencias del entorno

La integracion requiere dependencias del sistema dentro de la imagen Docker. Por ello, no basta con instalar el paquete Python: el contenedor debe incluir tambien las librerias necesarias para el renderizado.

## 7. Estrategia general ante integraciones externas

GreenPath sigue una serie de principios comunes para el uso de APIs y servicios externos:

- el flujo principal del negocio no debe depender de un tercero cuando no sea imprescindible
- las credenciales deben mantenerse fuera de codigo
- los fallos deben dejar rastro en logs
- el frontend no debe asumir que una integracion siempre existe
- la documentacion debe explicar claramente que integra, como y con que limites

## 8. Variables de entorno relacionadas

Resumen de variables clave:

| Variable | Uso |
| --- | --- |
| `GOOGLE_MAPS_API_KEY` | Geocodificacion y optimizacion con Google |
| `GMAIL_FROM` | Remitente de los correos |
| `GMAIL_CLIENT_SECRET_JSON` | Cliente OAuth de Gmail API |
| `GMAIL_TOKEN_JSON` | Token OAuth para envio real |

## 9. Impacto academico de estas integraciones

Desde la perspectiva del TFG, estas integraciones aportan valor porque demuestran:

- capacidad de integrar servicios externos reales
- criterio para decidir que partes del sistema deben tolerar fallos externos
- manejo de configuracion sensible
- coordinacion entre backend, frontend y procesos asincronos
- generacion documental con calidad suficiente para un caso de uso real

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
- correcto almacenamiento y regeneracion del PDF

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
- Gmail API permite un canal formal de notificacion sin depender de envio local improvisado
- WeasyPrint permite facturas PDF mantenibles a partir de HTML y CSS versionables

Estas elecciones se consideran razonables para un TFG porque aportan valor funcional visible sin exigir una infraestructura desproporcionada.

## 13. Documentos relacionados

Para ampliar esta informacion conviene consultar tambien:

- `docs/API.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/ROUTE_FLOW.md`
- `docs/MEMORIA_FUNCIONAL_TFG.md`
- `docs/DESPLIEGUE_Y_OPERACION.md`
- `docs/BIBLIOGRAFIA_Y_FUENTES.md`

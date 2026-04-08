# Indice de Documentacion GreenPath

Fecha de revision: 2026-04-08

Este documento sirve como mapa de lectura de la documentacion del proyecto.
Actualmente la documentacion central del sistema se mantiene de forma unificada en la carpeta `docs/` del backend y cubre negocio, requisitos, arquitectura, API, frontend, testing, integraciones, planificacion, despliegue, manual de usuario, bibliografia y modelo de datos.

## 1. Por donde empezar

Si vienes nuevo al proyecto, el orden recomendado es:

1. `README.md`
2. `docs/FUNCIONAL.md`
3. `docs/ARQUITECTURA_TECNICA.md`
4. `docs/API.md`
5. `docs/FRONTEND_PANTALLAS.md`
6. `docs/REQUISITOS.md`
7. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
8. `docs/PLANIFICACION_Y_COSTES.md`
9. `docs/TESTING.md`
10. `docs/ROUTE_FLOW.md`
11. `docs/CASOS_DE_USO.md`
12. `docs/MANUAL_USUARIO.md`
13. `docs/HISTORIAS_USUARIO.md`
14. `docs/MEMORIA_FUNCIONAL_TFG.md`
15. `docs/DESPLIEGUE_Y_OPERACION.md`
16. `docs/BIBLIOGRAFIA_Y_FUENTES.md`
17. `docs/UML_BD.md`

## 2. Descripcion de cada documento

### `README.md`

Resumen ejecutivo del proyecto:

- que es GreenPath
- que cubre hoy
- stack
- mapa de documentacion
- puesta en marcha
- estado actual de testing automatizado

### `docs/FUNCIONAL.md`

Documento funcional principal.
Es la referencia mas importante para entender:

- vision del producto
- roles
- modulos
- procesos de negocio
- reglas de negocio
- alcance actual

### `docs/ARQUITECTURA_TECNICA.md`

Documento tecnico de arquitectura.
Explica:

- distribucion por apps
- flujo tecnico de rutas, recogidas y ventas
- integraciones externas
- seguridad y observabilidad

### `docs/API.md`

Documento de endpoints y contratos.
Util para:

- frontend
- integraciones
- validacion manual
- testing

### `docs/FRONTEND_PANTALLAS.md`

Inventario del frontend.
Describe:

- rutas de pantalla
- archivos principales
- estado de implementacion
- notas de comportamiento por modulo

### `docs/REQUISITOS.md`

Catalogo formal de requisitos del proyecto.
Explica:

- requisitos de negocio
- requisitos de informacion
- requisitos funcionales
- requisitos no funcionales
- requisitos de interfaz
- requisitos de integracion
- requisitos de seguridad y trazabilidad

### `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`

Documento especifico de integraciones.
Explica:

- APIs externas utilizadas
- para que se usa cada una
- variables de entorno implicadas
- riesgos y comportamiento ante fallos
- encaje academico de estas integraciones

### `docs/PLANIFICACION_Y_COSTES.md`

Documento academico de organizacion del trabajo.
Explica:

- metodologia adoptada
- fases del proyecto
- estimacion de esfuerzo
- cronograma orientativo
- valoracion de costes
- riesgos y desviaciones

### `docs/DESPLIEGUE_Y_OPERACION.md`

Documento orientado a explotacion y soporte.
Explica:

- estructura de servicios
- variables de entorno
- puesta en marcha
- operacion diaria
- observabilidad
- backup y recuperacion
- checklist de defensa o demo

### `docs/BIBLIOGRAFIA_Y_FUENTES.md`

Documento de apoyo academico.
Explica:

- fuentes oficiales del stack
- referencias de integraciones externas
- fuentes para testing y PDF
- base bibliografica del TFG

### `docs/TESTING.md`

Documento operativo de testing.
Explica:

- estrategia actual
- estructura de suites
- cobertura backend y frontend
- comandos recomendados
- huecos aun manuales
- prioridades de ampliacion

### `docs/CASOS_DE_USO.md`

Documento de comportamiento por actor.
Explica:

- flujos principales del owner
- flujos principales del worker
- flujos del client
- procesos automaticos del sistema

### `docs/MANUAL_USUARIO.md`

Manual funcional de uso.
Explica:

- como se usa la aplicacion por rol
- que acciones puede hacer cada usuario
- recomendaciones de uso
- problemas habituales y resolucion basica

### `docs/ROUTE_FLOW.md`

Documento especializado en rutas.
Es el mejor lugar para revisar:

- generacion semanal
- overview operativo
- ejecucion diaria
- reglas del modulo de rutas

### `docs/HISTORIAS_USUARIO.md`

Backlog funcional priorizado.
Recoge historias y criterios de aceptacion por rol.

### `docs/MEMORIA_FUNCIONAL_TFG.md`

Documento redactado con tono mas academico y de memoria.
Es util para:

- entrega del TFG
- defensa del proyecto
- explicar el valor del sistema mas alla de la API y el codigo
- enlazar de forma coherente la parte funcional, tecnica y de planificacion

### `docs/UML_BD.md`

Diagrama UML de base de datos.
Es util para:

- entender entidades y relaciones
- revisar cardinalidades
- apoyar explicaciones tecnicas y academicas
- visualizar el modelo persistente del sistema

## 3. Recomendacion para defensa o entrega

Si el objetivo es presentar el proyecto de forma profesional:

- usa `docs/FUNCIONAL.md` como base de explicacion del negocio
- utiliza `docs/REQUISITOS.md` para justificar el catalogo formal de requisitos
- utiliza `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md` para justificar APIs y dependencias externas
- utiliza `docs/DESPLIEGUE_Y_OPERACION.md` para justificar puesta en marcha, operacion y continuidad
- utiliza `docs/PLANIFICACION_Y_COSTES.md` para justificar metodologia, estimaciones y costes
- utiliza `docs/BIBLIOGRAFIA_Y_FUENTES.md` para apoyar bibliografia y referencias
- apoya la parte tecnica con `docs/ARQUITECTURA_TECNICA.md`
- utiliza `docs/API.md` para justificar contratos y endpoints
- utiliza `docs/FRONTEND_PANTALLAS.md` para demostrar cobertura funcional del front
- utiliza `docs/TESTING.md` para justificar validacion automatizada y calidad
- utiliza `docs/CASOS_DE_USO.md` para explicar secuencias funcionales de actores
- utiliza `docs/MANUAL_USUARIO.md` como anexo de uso
- utiliza `docs/MEMORIA_FUNCIONAL_TFG.md` como hilo academico de sintesis
- utiliza `docs/UML_BD.md` para apoyar la explicacion del modelo de datos

## 4. Lectura segun objetivo

### Si tu objetivo es entender el negocio

Lee en este orden:

1. `README.md`
2. `docs/FUNCIONAL.md`
3. `docs/REQUISITOS.md`
4. `docs/CASOS_DE_USO.md`
5. `docs/HISTORIAS_USUARIO.md`
6. `docs/MEMORIA_FUNCIONAL_TFG.md`
7. `docs/DESPLIEGUE_Y_OPERACION.md`
8. `docs/BIBLIOGRAFIA_Y_FUENTES.md`
9. `docs/UML_BD.md`

### Si tu objetivo es entrar a desarrollar backend

Lee en este orden:

1. `README.md`
2. `docs/ARQUITECTURA_TECNICA.md`
3. `docs/API.md`
4. `docs/REQUISITOS.md`
5. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
6. `docs/PLANIFICACION_Y_COSTES.md`
7. `docs/TESTING.md`
8. `docs/ROUTE_FLOW.md`
9. `docs/CASOS_DE_USO.md`
10. `docs/DESPLIEGUE_Y_OPERACION.md`
11. `docs/UML_BD.md`

### Si tu objetivo es entrar a desarrollar frontend

Lee en este orden:

1. `README.md`
2. `docs/FRONTEND_PANTALLAS.md`
3. `docs/API.md`
4. `docs/REQUISITOS.md`
5. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
6. `docs/PLANIFICACION_Y_COSTES.md`
7. `docs/TESTING.md`
8. `docs/ROUTE_FLOW.md`
9. `docs/MANUAL_USUARIO.md`
10. `docs/DESPLIEGUE_Y_OPERACION.md`
11. `docs/UML_BD.md`

### Si tu objetivo es preparar entrega o defensa

Lee en este orden:

1. `README.md`
2. `docs/FUNCIONAL.md`
3. `docs/REQUISITOS.md`
4. `docs/INTEGRACIONES_Y_APIS_EXTERNAS.md`
5. `docs/PLANIFICACION_Y_COSTES.md`
6. `docs/MEMORIA_FUNCIONAL_TFG.md`
7. `docs/ARQUITECTURA_TECNICA.md`
8. `docs/TESTING.md`
9. `docs/CASOS_DE_USO.md`
10. `docs/MANUAL_USUARIO.md`
11. `docs/DESPLIEGUE_Y_OPERACION.md`
12. `docs/BIBLIOGRAFIA_Y_FUENTES.md`
13. `docs/UML_BD.md`

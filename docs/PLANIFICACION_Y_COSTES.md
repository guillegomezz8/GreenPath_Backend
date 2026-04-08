# Organizacion, Planificacion y Costes GreenPath

Fecha de revision: 2026-04-08

## 1. Objetivo del documento

Este documento cubre una parte especialmente importante para una memoria de TFG formal: la metodologia de trabajo, la planificacion temporal, las estimaciones de esfuerzo, la valoracion economica del proyecto y varios indicadores cuantitativos que ayudan a defender la entidad real del desarrollo.

No pretende reconstruir con precision contable cada hora invertida, sino ofrecer una planificacion razonada, una estimacion profesional del esfuerzo y una lectura creible del coste de desarrollo de GreenPath como producto software.

## 2. Resumen ejecutivo de planificacion

GreenPath puede entenderse como un proyecto full-stack con las siguientes caracteristicas de gestion:

- desarrollo iterativo e incremental
- un dominio de negocio con reglas que evolucionan durante el proyecto
- necesidad de equilibrar backend, frontend, integraciones, testing y documentacion
- importancia especial del uso movil en el modulo de rutas
- crecimiento del alcance al incorporar la capa economica de ventas y facturacion

Esto justifica que la planificacion no se haya concebido como una secuencia totalmente lineal, sino como una organizacion por bloques funcionales y por hitos de valor.

## 3. Revision de metodologias y enfoque elegido

### 3.1 Alternativas metodologicas consideradas

| Enfoque | Ventajas | Inconvenientes en este proyecto |
| --- | --- | --- |
| Cascada | Claridad documental y secuencia ordenada | Poco flexible ante cambios funcionales y de UX |
| Modelo en V | Buena relacion entre desarrollo y validacion | Menor adaptabilidad a refinamiento progresivo del dominio |
| Agil iterativo | Permite revisar alcance y validar por entregas | Requiere disciplina para mantener trazabilidad documental |

### 3.2 Metodologia seleccionada

Para GreenPath se adopto un enfoque agil adaptado a un proyecto academico individual, con estas caracteristicas:

- trabajo por bloques funcionales
- validacion progresiva del resultado
- ajustes frecuentes sobre reglas de negocio y experiencia de usuario
- documentacion paralela a la implementacion
- testing y estabilizacion no relegados al final

### 3.3 Justificacion del enfoque

Esta eleccion se justifica porque el proyecto presenta varios factores de incertidumbre controlada:

- necesidad de afinar la logica de generacion semanal
- importancia de refinar el responsive de ejecucion de ruta
- aparicion posterior del bloque de ventas y facturacion
- dependencias con servicios externos opcionales

Con un modelo excesivamente rigido, estas revisiones habrian resultado mas costosas y menos naturales.

## 4. Gobierno del proyecto y roles de trabajo

Aunque el desarrollo se ha realizado esencialmente de forma individual, es util explicitar que funciones han existido dentro del proyecto:

| Rol | Responsabilidad principal |
| --- | --- |
| Desarrollador principal | Analisis, backend, frontend, testing y documentacion |
| Product owner funcional | Priorizacion de necesidades del negocio y validacion del valor funcional |
| Revisor academico | Enfoque metodologico, calidad de la memoria y coherencia tecnica |
| Usuario de negocio de referencia | Validacion del encaje real de los flujos operativos |

Esta descomposicion es util porque ayuda a explicar que el proyecto no solo consistia en programar, sino tambien en priorizar, validar, corregir y documentar.

## 5. Supuestos de planificacion

Para construir una estimacion coherente se han tomado los siguientes supuestos:

- proyecto desarrollado principalmente por una sola persona
- alcance full-stack: backend, frontend, integraciones, testing y documentacion
- necesidad de preparar una entrega academica, no solo un prototipo tecnico
- carga total de referencia: 300 horas de trabajo

La cifra de 300 horas se usa como referencia academica razonable para un TFG de ingenieria de software y permite ordenar el esfuerzo por fases y por entregables.

## 6. Estructura por fases

### 6.1 Fases principales

| Fase | Descripcion | Entregable principal |
| --- | --- | --- |
| Estudio previo | Comprension del dominio y delimitacion del alcance | Vision inicial del sistema |
| Analisis funcional | Roles, entidades, procesos y reglas | Modelo funcional base |
| Diseno tecnico | Arquitectura, stack, estructura por apps e interfaz | Base tecnica del proyecto |
| Implementacion del nucleo operativo | Clientes, trabajadores, camiones, zonas, rutas, solicitudes y recogidas | Flujo core del negocio |
| Implementacion del bloque economico | Compradores, ventas, facturas PDF y estadisticas | Cierre economico del sistema |
| Testing y estabilizacion | Pruebas, correcciones, endurecimiento y responsive | Version mas robusta |
| Documentacion y entrega | Memoria, anexos, README y materiales de defensa | Paquete final del TFG |

### 6.2 Dependencias entre fases

Aunque las fases se listan por separado, en la practica no fueron compartimentos estancos. Hubo dependencias claras:

- el analisis alimenta el diseno
- el diseno condiciona backend y frontend
- la implementacion obliga a revisar parte del analisis
- el testing descubre ajustes funcionales y tecnicos
- la documentacion no puede posponerse completamente al final

Por eso, la planificacion debe leerse como una guia ordenadora del trabajo y no como una secuencia inflexible.

## 7. Entregables por fase

| Fase | Entregables principales |
| --- | --- |
| Estudio previo | descripcion del problema, alcance inicial, stack candidato |
| Analisis funcional | documentos de roles, modulos, reglas y procesos |
| Diseno tecnico | estructura por apps, criterios de interfaz, arquitectura de alto nivel |
| Implementacion operativa | CRUD maestros, rutas, solicitudes, recogidas, ejecucion diaria |
| Implementacion economica | buyers, sales, PDF, settings economicos, resumen economico |
| Testing y estabilizacion | suites backend/frontend, repaso de admins, ajuste responsive |
| Documentacion y entrega | memoria, indice documental, README, guias y anexos |

## 8. Planificacion temporal orientativa

### 8.1 Cronograma por semanas

La siguiente planificacion es una propuesta razonable de organizacion temporal:

| Semana | Contenido principal |
| --- | --- |
| 1 | Estudio previo del dominio y definicion del alcance |
| 2 | Analisis funcional de roles, entidades y flujos |
| 3 | Diseno tecnico, stack, estructura por apps y lineas de interfaz |
| 4 | Datos maestros: usuarios, clientes, trabajadores y camiones |
| 5 | Zonas, rutas plantilla y base geoespacial |
| 6 | Generacion semanal y overview operativo |
| 7 | Ejecucion diaria de ruta y recogidas |
| 8 | Solicitudes al cliente y automatizacion con Celery |
| 9 | Medicion posterior, facturable y resumen economico base |
| 10 | Compradores, ventas y facturas PDF |
| 11 | Testing, refactor, ajustes responsive y admins |
| 12 | Documentacion, memoria, anexos y preparacion de entrega |

### 8.2 Hitos del proyecto

| Hito | Resultado esperado |
| --- | --- |
| H1 | Datos maestros estabilizados |
| H2 | Rutas plantilla y zonas operativas |
| H3 | Generacion semanal funcional |
| H4 | Ejecucion diaria usable en movil |
| H5 | Recogidas con medicion y criterio facturable |
| H6 | Ventas y facturas PDF operativas |
| H7 | Estadisticas con coste, ingreso y beneficio |
| H8 | Suite inicial de tests y documentacion consolidada |

### 8.3 Naturaleza iterativa del calendario

Aunque el cronograma se expresa por semanas para facilitar su lectura academica, el trabajo real puede implicar solapamientos. Por ejemplo:

- la documentacion puede avanzar desde etapas tempranas
- el testing puede empezar antes de concluir toda la implementacion
- el feedback sobre rutas puede forzar iteraciones en frontend y backend a la vez

Por ello, la planificacion temporal debe entenderse como una distribucion de foco principal, no como una prohibicion de solapamientos.

## 9. Estimacion de esfuerzo

### 9.1 Estimacion por fase

| Fase | Horas estimadas | Porcentaje |
| --- | ---: | ---: |
| Estudio previo | 20 | 6,7 % |
| Analisis funcional | 35 | 11,7 % |
| Diseno tecnico y UX | 30 | 10,0 % |
| Implementacion backend del nucleo operativo | 70 | 23,3 % |
| Implementacion frontend y responsive | 45 | 15,0 % |
| Bloque economico y facturacion | 30 | 10,0 % |
| Testing y estabilizacion | 25 | 8,3 % |
| Documentacion y preparacion de defensa | 45 | 15,0 % |
| **Total** | **300** | **100 %** |

### 9.2 Estimacion por disciplina

| Disciplina | Horas estimadas | Porcentaje |
| --- | ---: | ---: |
| Analisis y modelado | 45 | 15,0 % |
| Backend | 95 | 31,7 % |
| Frontend | 60 | 20,0 % |
| Integraciones externas y PDF | 25 | 8,3 % |
| Testing y estabilizacion | 30 | 10,0 % |
| Documentacion | 45 | 15,0 % |
| **Total** | **300** | **100 %** |

### 9.3 Estimacion por grandes bloques funcionales

| Bloque | Horas estimadas |
| --- | ---: |
| Datos maestros: clientes, trabajadores, camiones, zonas | 45 |
| Rutas, generacion semanal y operacion diaria | 75 |
| Solicitudes, recogidas y medicion | 45 |
| Compradores, ventas y facturacion PDF | 35 |
| Configuracion global y estadisticas | 25 |
| Testing, refactor y endurecimiento | 30 |
| Documentacion y entrega | 45 |
| **Total** | **300** |

### 9.4 Lectura de la distribucion

Esta distribucion refleja varias ideas importantes:

- el mayor peso del proyecto recae en el nucleo operativo
- el frontend tiene un peso relevante por la exigencia responsive
- el bloque economico no es accesorio, sino una ampliacion significativa
- documentacion y defensa consumen un volumen de esfuerzo real
- testing y estabilizacion merecen una fase explicita

## 10. Estadisticas e indicadores del proyecto

### 10.1 Snapshot estructural a fecha 2026-04-05

| Indicador | Valor |
| --- | ---: |
| Apps backend de dominio | 9 |
| Modulos o paginas principales en frontend | 14 |
| Documentos centralizados en `docs/` | 14 |
| Fixtures JSON de demo | 13 |
| Integraciones externas principales | 3 |
| Tests backend documentados | 25 |
| Tests frontend documentados | 17 |
| Archivos de test frontend detectados | 12 |

### 10.2 Interpretacion de estos indicadores

Estos datos sirven para justificar la entidad real del proyecto:

- no se trata de una unica app monolitica, sino de un sistema modular
- el frontend tiene una cobertura funcional amplia por modulos
- existe un paquete documental centralizado y mantenido
- ese paquete documental ya no se limita a descripcion tecnica: incluye requisitos, casos de uso, manual de usuario, testing, integraciones y planificacion
- hay base de datos demo y testing automatizado en ambas capas

### 10.3 Indicadores de complejidad funcional

Desde una lectura de producto, GreenPath combina al menos:

- 3 roles de usuario con experiencias diferentes
- flujos operativos y economicos diferenciados
- datos geograficos y documentales
- tareas sincronicamente visibles y asincronas
- integraciones externas opcionales pero utiles

Esto refuerza la idea de que el proyecto tiene suficiente profundidad para una memoria academica extensa.

## 11. Estimacion de costes del proyecto

### 11.1 Criterio de valoracion

La siguiente estimacion no representa necesariamente gasto real abonado durante el TFG. Su objetivo es valorar GreenPath como si se tratara de un proyecto software encargado a un perfil tecnico full-stack, incluyendo el coste del tiempo de desarrollo y una valoracion razonable de infraestructura y soporte.

### 11.2 Coste de personal

Se propone una estimacion conservadora basada en varios tipos de actividad:

| Categoria | Horas | Tarifa orientativa | Coste |
| --- | ---: | ---: | ---: |
| Analisis y diseno | 85 | 20 EUR/h | 1.700 EUR |
| Implementacion full-stack | 145 | 22 EUR/h | 3.190 EUR |
| Testing y estabilizacion | 25 | 18 EUR/h | 450 EUR |
| Documentacion y preparacion de defensa | 45 | 15 EUR/h | 675 EUR |
| **Total personal** | **300** |  | **6.015 EUR** |

### 11.3 Costes de infraestructura y herramientas

| Concepto | Estimacion |
| --- | ---: |
| Equipo de desarrollo amortizado | 350 EUR |
| Electricidad, conectividad e imprevistos | 120 EUR |
| Entorno de despliegue, dominio o alojamiento basico | 80 EUR |
| Servicios externos y cuotas variables de integracion | 100 EUR |
| Licencias de software base | 0 EUR |
| **Total infraestructura y servicios** | **650 EUR** |

### 11.4 Costes indirectos

En una valoracion profesional conviene contemplar tambien costes indirectos asociados a coordinacion, revision, margen de contingencia y tiempo no productivo. Se propone una reserva del 15 % sobre el coste de personal:

- 15 % de 6.015 EUR = 902,25 EUR

Se redondea a:

- **900 EUR**

### 11.5 Coste total estimado

| Concepto | Coste |
| --- | ---: |
| Personal | 6.015 EUR |
| Infraestructura y servicios | 650 EUR |
| Costes indirectos y contingencia | 900 EUR |
| **Total estimado del proyecto** | **7.565 EUR** |

### 11.6 Escenarios de coste

| Escenario | Interpretacion | Coste orientativo |
| --- | --- | ---: |
| Conservador | Valor minimo razonable del proyecto | 6.800 EUR |
| Base | Estimacion principal defendible | 7.565 EUR |
| Ampliado | Con mayor peso de soporte, revision y contingencia | 8.400 EUR |

### 11.7 Lectura correcta de esta estimacion

Esta cifra debe entenderse como una aproximacion academica y profesional al valor del trabajo realizado. No implica que el TFG haya requerido exactamente ese desembolso real, sino que permite defender que el proyecto tiene entidad suficiente como desarrollo de software completo.

## 12. Riesgos de planificacion y mitigaciones

| Riesgo | Impacto | Mitigacion |
| --- | --- | --- |
| Crecimiento del alcance | Alto | Priorizar por bloques y cerrar iteraciones |
| Dependencia de APIs externas | Medio | Disenar fallbacks y tolerancia funcional |
| Complejidad del modulo de rutas | Alto | Documentacion especializada y tests dedicados |
| UX movil mas costosa de lo previsto | Alto | Revisiones iterativas y separacion de pantallas |
| Sobrecarga documental al final | Medio | Repartir documentacion y no concentrarla toda en un solo fichero |
| Ajuste del PDF mas largo de lo esperado | Medio | Iterar plantilla y aislar el problema en el modulo de ventas |

## 13. Desviaciones razonables respecto a una planificacion inicial

En un proyecto de estas caracteristicas es razonable esperar desviaciones en algunos puntos:

- ampliacion del bloque economico una vez consolidada la operacion
- mayor esfuerzo en responsive del previsto inicialmente
- tiempo adicional en ajuste del PDF de facturas
- necesidad de reforzar testing y admin cuando el producto madura
- mayor peso documental al aproximarse la entrega academica

Estas desviaciones no deben leerse como fallos de gestion, sino como consecuencia natural de un proyecto iterativo que evoluciona sobre un dominio real.

## 14. Indicadores de calidad de planificacion

Una planificacion de calidad no se mide solo por cumplir un calendario ideal, sino por mantener control sobre el proyecto. En GreenPath, los siguientes indicadores ayudan a argumentar esa calidad:

- existencia de una separacion clara entre documentos funcionales, tecnicos, testing y memoria
- modularidad tanto en backend como en frontend
- presencia de testing automatizado en ambas capas
- consolidacion de un indice documental unificado
- capacidad de absorber nuevas necesidades sin rehacer por completo la arquitectura

## 15. Recomendacion para memoria final de entrega

Si se prepara una memoria final en PDF, este documento puede alimentar directamente un capitulo de `Organizacion y planificacion`, incluyendo:

- metodologia seleccionada
- fases y cronograma
- estimacion de esfuerzo
- indicadores del proyecto
- valoracion economica
- riesgos y desviaciones

De esta forma, la memoria del TFG gana cuerpo academico sin sobrecargar el documento funcional principal ni la memoria de sintesis.

## 16. Relacion con el paquete documental del proyecto

La utilidad de este documento aumenta cuando se lee junto a:

- `docs/FUNCIONAL.md`, para entender el valor de negocio de lo planificado
- `docs/REQUISITOS.md`, para conectar esfuerzo con alcance y prioridad
- `docs/TESTING.md`, para vincular planificacion y validacion
- `docs/DESPLIEGUE_Y_OPERACION.md`, para justificar el esfuerzo de puesta en marcha y soporte
- `docs/MEMORIA_FUNCIONAL_TFG.md`, para llevar estas ideas a una redaccion mas academica

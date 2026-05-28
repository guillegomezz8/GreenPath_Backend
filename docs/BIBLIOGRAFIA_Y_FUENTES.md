# Bibliografia y Fuentes GreenPath

Fecha de revision: 2026-05-27

## 1. Objetivo del documento

Este documento recoge las fuentes tecnicas y de referencia utilizadas para el desarrollo, diseno y documentacion del proyecto.
Su finalidad es apoyar la parte academica del TFG y dejar trazabilidad sobre la base documental utilizada.

## 2. Fuentes de arquitectura y backend

### 2.1 Django

- Django Software Foundation. *Django documentation*. https://docs.djangoproject.com/

### 2.2 Django REST Framework

- Encode OSS Ltd. *Django REST framework documentation*. https://www.django-rest-framework.org/

### 2.3 Django Filter

- *django-filter documentation*. https://django-filter.readthedocs.io/

### 2.4 PostgreSQL

- The PostgreSQL Global Development Group. *PostgreSQL documentation*. https://www.postgresql.org/docs/

### 2.5 PostGIS

- The PostGIS Project. *PostGIS documentation*. https://postgis.net/documentation/

### 2.6 Celery

- Celery Project. *Celery documentation*. https://docs.celeryq.dev/

### 2.7 Redis

- Redis Ltd. *Redis documentation*. https://redis.io/docs/

### 2.8 Simple JWT

- Jazzband. *djangorestframework-simplejwt documentation*. https://django-rest-framework-simplejwt.readthedocs.io/

## 3. Fuentes de frontend

### 3.1 React

- Meta Open Source. *React documentation*. https://react.dev/

### 3.2 Vite

- Vite Team. *Vite documentation*. https://vite.dev/

### 3.3 Tailwind CSS

- Tailwind Labs. *Tailwind CSS documentation*. https://tailwindcss.com/docs/

### 3.4 Leaflet

- Leaflet. *Leaflet documentation*. https://leafletjs.com/reference.html

### 3.5 React Leaflet

- React Leaflet. *Documentation*. https://react-leaflet.js.org/

## 4. Integraciones externas

### 4.1 Google Maps Platform

- Google. *Maps Platform documentation*. https://developers.google.com/maps/documentation
- Google. *Directions API documentation*. https://developers.google.com/maps/documentation/directions
- Google. *Geocoding API documentation*. https://developers.google.com/maps/documentation/geocoding

### 4.2 Gmail API

- Google. *Gmail API documentation*. https://developers.google.com/gmail/api
- Google. *Using OAuth 2.0 to Access Google APIs*. https://developers.google.com/identity/protocols/oauth2

### 4.3 Google Identity Services

- Google. *Google Identity Services for Web*. https://developers.google.com/identity/gsi/web/guides/client-library
- Google. *Display the Sign In With Google button*. https://developers.google.com/identity/gsi/web/guides/display-button

## 5. Generacion documental y PDF

### 5.1 WeasyPrint

- CourtBouillon. *WeasyPrint documentation*. https://doc.courtbouillon.org/weasyprint/

## 5.2 Infraestructura y contenedores

### Docker

- Docker Inc. *Docker documentation*. https://docs.docker.com/

### Docker Compose

- Docker Inc. *Docker Compose documentation*. https://docs.docker.com/compose/

## 6. Testing y calidad

### 6.1 Pytest y testing en Python

- pytest-dev. *pytest documentation*. https://docs.pytest.org/

### 6.2 Vitest

- Vitest. *Vitest documentation*. https://vitest.dev/

### 6.3 Testing Library

- Testing Library. *Documentation*. https://testing-library.com/docs/

## 7. Referencias del propio proyecto

Los siguientes documentos forman parte de la base documental interna de GreenPath y sirven como fuente primaria del propio TFG:

- `README.md`
- `docs/FUNCIONAL.md`
- `docs/REQUISITOS.md`
- `docs/ARQUITECTURA_TECNICA.md`
- `docs/API.md`
- `docs/FRONTEND_PANTALLAS.md`
- `docs/ROUTE_FLOW.md`
- `docs/PLANIFICACION_Y_COSTES.md`
- `docs/TESTING.md`
- `docs/UML_BD.md`

## 8. Uso academico recomendado de estas fuentes

Estas fuentes pueden utilizarse para:

- justificar decisiones tecnologicas
- apoyar explicaciones de arquitectura
- documentar integraciones externas
- reforzar la seccion metodologica y de calidad
- construir bibliografia de la memoria final

## 8.1 Fuentes especialmente valiosas para defender la complejidad tecnica

En el caso concreto de GreenPath, conviene dar un peso especial a varias familias de fuentes, porque son las que mejor ayudan a justificar que el proyecto va mas alla de una aplicacion CRUD simple:

- documentacion de Google Maps Platform, por el papel de la geocodificacion, la optimizacion y la navegacion externa
- documentacion de Celery y Redis, por la existencia de tareas asincronas reales y arquitectura de soporte
- documentacion de Leaflet y React Leaflet, por la capa cartografica embebida en el frontend
- documentacion de WeasyPrint, por la generacion documental en PDF a partir de HTML/CSS
- documentacion de Django REST Framework, por el peso de la API como capa contractual y de negocio

Estas referencias son especialmente utiles en la memoria del TFG cuando se quiere argumentar que la complejidad del sistema no depende solo del numero de modulos, sino tambien de las integraciones y librerias especializadas que se han incorporado.

## 9. Observaciones

- Siempre que sea posible conviene citar documentacion oficial de la herramienta o servicio utilizado.
- Para la memoria final del TFG puede adaptarse este documento al formato bibliografico exigido por la universidad o por el tutor.
- Este documento no sustituye a la explicacion tecnica del proyecto, sino que la apoya con referencias verificables.
- Para la defensa oral del TFG, resulta especialmente recomendable enlazar estas fuentes con decisiones concretas tomadas en GreenPath y no dejarlas como una lista aislada de tecnologias.

# Django Base Project

  

Este proyecto es una base sólida en Django que cuenta con un módulo de usuarios extendido, implementaciones de seguridad mediante JWT, y una estructura modular que facilita la escalabilidad y mantenimiento a largo plazo.

  

## Estructura del Proyecto

  

El proyecto sigue una estructura modular organizada de la siguiente manera:

  

-  **Proyecto base**: La carpeta principal del proyecto contiene la configuración global, URLs, y utilidades compartidas.

-  **Apps**: Una carpeta llamada `apps` a nivel de proyecto donde se encuentran los módulos de cada funcionalidad. Actualmente incluye los módulos `user` y `base`, pero puedes agregar otros módulos en esta estructura de forma sencilla.

  

### Carpetas y Archivos Principales

  

1.  **`apps/user`**:

- Extiende el usuario predeterminado de Django, añadiendo atributos personalizados como nombre, apellidos, email, etc.

- Incluye un sistema de autenticación mediante `JWT`.

- Implementa serializadores y vistas basadas en ViewSets para gestionar las operaciones CRUD de los usuarios.

2.  **`apps/base`**:

- Proporciona un modelo base reutilizable para todos los futuros modelos del proyecto.

- Este modelo base incluye:

- Un identificador único (ID).

- Fechas de creación, modificación y borrado lógico (soft delete).

- Atributo `is_active` para habilitar o deshabilitar entidades.

- Historial de modificaciones para trazabilidad.

  

3.  **`media/`**: Carpeta destinada a almacenar archivos subidos, como imágenes de perfil de usuario o documentos enviados a través de formularios.

  

4.  **`settings/`**:

- Contiene las configuraciones del proyecto, tanto para el entorno local como para despliegue en producción.

- Se puede cambiar fácilmente entre configuraciones locales y de despliegue según sea necesario.

  

5.  **`urls.py`**:

- En este archivo se definen las rutas generales del proyecto.

- Incluye los routers de los diferentes módulos y URLs específicas.

- Ejemplo de URLs: `/users/`, `/shops/`, etc.

## Características Clave

  

### Autenticación con JWT

  

El proyecto implementa autenticación mediante **JSON Web Tokens (JWT)**. Al iniciar sesión, el usuario recibe un token que puede utilizar en las solicitudes a los endpoints que requieren autenticación.

  

#### Proceso de Autenticación:

1. Realiza una petición POST a `/login/` con el usuario y la contraseña.

2. Recibe un **JWT** en la respuesta.

3. Usa el JWT en las solicitudes protegidas, añadiendo el token en los encabezados de las peticiones:

```http

Authorization: Bearer <your_token_here>
```

  

#### Swagger para Documentación de API

El proyecto incluye documentación interactiva de la API mediante Swagger, accesible desde /docs. Esto permite ver los endpoints disponibles y realizar pruebas desde el navegador.

  

Para realizar peticiones a endpoints protegidos, pega el token JWT generado durante el login en el campo de jwtAuth dentro del Swagger.

  

## Módulo de Usuarios

  

El módulo de usuarios amplía el modelo de usuario estándar de Django, añadiendo nuevos campos como nombre, apellidos y email, además de las funcionalidades estándar de login, registro y administración de usuarios.

  

-  **Endpoints principales del usuario**:

-  `POST /users/`: Registrar un nuevo usuario.

-  `POST /login/`: Iniciar sesión y obtener un JWT.

-  `GET /users/`: Listar todos los usuarios (requiere autenticación).

-  `PUT /users/{id}/`: Actualizar información de un usuario (requiere autenticación).

-  `DELETE /users/{id}/`: Deshabilitar un usuario (borrado lógico) (requiere autenticación).

  

### Módulo Base

  

El módulo base contiene utilidades comunes para reutilizar en todo el proyecto:

  

- Un **modelo base** que incluye campos como:

-  `created_date`: Fecha de creación.

-  `modified_date`: Fecha de la última modificación.

-  `deleted_date`: Fecha de eliminación lógica.

-  `is_active`: Atributo que permite habilitar/deshabilitar entidades sin eliminarlas físicamente de la base de datos.

- Este modelo base puede ser heredado por cualquier otro modelo en el futuro para evitar la duplicación de código.

  

## Estructura de las Apps

  

Las apps siguen una organización clara para mantener el código modular y escalable:

- Cada módulo (app) contiene las siguientes carpetas clave:

-  **`serializers/`**: Define cómo se serializan y deserializan los datos para las operaciones de API.

-  **`viewsets/`**: Define las vistas basadas en ViewSets, que gestionan las operaciones CRUD del modelo correspondiente.

  

### Ejemplo de Módulos Actuales:

1.  **User**:

- Contiene la lógica para la gestión de usuarios (registro, login, perfil, etc.).

- Extiende el modelo de usuario predeterminado de Django para agregar campos personalizados.

2.  **Base**:

- Contiene utilidades comunes como el modelo base mencionado anteriormente.

  

## Despliegue y Configuración

  

El proyecto cuenta con una carpeta `settings/` donde se especifican diferentes configuraciones según el entorno de desarrollo o producción. Esto facilita el despliegue en diferentes entornos.

  

### Configuración de Entornos

  

-  **Desarrollo**: Configuraciones predeterminadas para trabajar en local.

-  **Producción**: Configuraciones específicas para el despliegue en servidores con ajustes optimizados de seguridad y rendimiento.

  
  

## Desarrollo en local

Para poder levantar este proyecto en local se provee de un docker-compose.yml el cual deberemos ejecutar.

```sh

docker-compose  up
```
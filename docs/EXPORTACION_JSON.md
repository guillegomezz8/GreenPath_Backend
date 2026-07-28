# Exportacion JSON de GreenPath

Para generar una copia de los datos de negocio sin sesiones, permisos,
tokens, tareas de Celery ni historicos de Django:

```bash
python manage.py export_greenpath
```

Con el proyecto ejecutandose en Docker:

```bash
docker compose exec web python manage.py export_greenpath
```

El archivo se guarda en `exports/greenpath_export_FECHA_HORA.json`.

Tambien se puede elegir la ruta:

```bash
python manage.py export_greenpath --output copias/greenpath.json
```

El resultado mantiene el formato de fixture de Django y puede restaurarse
en una base de datos con las migraciones aplicadas:

```bash
python manage.py loaddata copias/greenpath.json
```

Los archivos contienen datos personales y hashes de contrasenas. Deben
guardarse en una ubicacion privada y no subirse al repositorio.

# Fixtures de demo

Carga recomendada:

1. `01-users.json`
2. `02-companies.json`
3. `03-workers.json`
4. `04-clients.json`
5. `05-routes.json`
6. `06-collections.json`
7. `07-zones.json`
8. `08-truck.json`
9. `09-company-hubs.json`
10. `10-route-zone-days.json`
11. `11-company-settings.json`
12. `12-buyers.json`
13. `13-sales.json`

Ejemplo de carga:

```bash
python manage.py loaddata \
  apps/user/fixtures/01-users.json \
  apps/user/fixtures/02-companies.json \
  apps/user/fixtures/03-workers.json \
  apps/user/fixtures/04-clients.json \
  apps/user/fixtures/05-routes.json \
  apps/user/fixtures/06-collections.json \
  apps/user/fixtures/07-zones.json \
  apps/user/fixtures/08-truck.json \
  apps/user/fixtures/09-company-hubs.json \
  apps/user/fixtures/10-route-zone-days.json \
  apps/user/fixtures/11-company-settings.json \
  apps/user/fixtures/12-buyers.json \
  apps/user/fixtures/13-sales.json
```

Notas:

- `11-company-settings.json` ya incluye datos fiscales demo para emitir facturas de venta desde el primer arranque.
- `12-buyers.json` crea compradores internos de ejemplo para el modulo de ventas.
- `13-sales.json` crea ventas demo con numero de factura manual y PDF descargable bajo demanda desde la API o el frontend.

- `06-collections.json` ahora prioriza recogidas recientes (febrero-abril 2026), con mayoria de bidones, algunos casos pendientes/cancelados y litros confirmados coherentes para alimentar estimaciones.
- `08-truck.json` se reduce a dos furgonetas operativas de demo.
- `13-sales.json` reparte exactamente los litros confirmados y facturables cargados en `06-collections.json`, para que la demo economica mantenga coherencia entre compra y venta.

## Compatibilidad con el backend actual

Aplicar migraciones antes de cargar los fixtures. `loaddata` restaura valores
persistidos y no ejecuta el `save()` de negocio para recalcular importes:
los datos de medicion, descuento y total deben ser coherentes en el JSON.
`measured_liters` representa litros finales pagables.

Este conjunto contiene 13 archivos y no incluye recogidas al por mayor.
Se pueden crear desde `/bulk-collections/` con un owner y modulo habilitado,
o restaurarlas desde `export_greenpath`. Su identificador de modelo Django
es `wholesale.bulkcollection`, aunque el paquete sea `apps.bulk_collection`.
Los adjuntos deben restaurarse por separado desde la copia de `MEDIA_ROOT`.

## Demo comercial ampliada sin sobrescribir datos

El nuevo archivo `demo_datos.json` contiene 2728 registros con referencias
simbolicas y fechas relativas. Se carga con un comando propio, no con
`loaddata`, para evitar que las PK de un fixture sustituyan filas existentes.

```bash
docker compose exec web python manage.py load_demo_data
```

Sin Docker:

```bash
python manage.py load_demo_data
```

Crea una empresa independiente `GreenPath Presentacion demo-clientes` con:

- 80 clientes y sus usuarios; 6 trabajadores y un owner;
- 7 vehiculos, 4 zonas con poligonos y hub geolocalizado en Sevilla;
- 6 rutas, 42 configuraciones por dia, 60 jornadas y 480 paradas/solicitudes;
- 1104 recogidas con estados y condiciones de facturacion variados;
- 72 compras al por mayor en litros, kilogramos y unidades;
- 8 compradores, 96 ventas y 192 lineas distribuidas por los ultimos 12 meses.

Los importes se recalculan con los modelos. Las ventas crean automaticamente
el snapshot fiscal. Las jornadas incluyen dias planificados, completos,
parciales y cancelados. No se envian correos, no se consulta Google, no se
programan tareas Celery y no se generan archivos adjuntos durante la carga.

Acceso a la demo (usuarios sin privilegios de admin):

| Rol | Usuario | Contrasena por defecto |
| --- | --- | --- |
| Owner | `propietario@demo.com` | `pass12345` |
| Worker | `demo-clientes-worker-1` (hasta `-6`) | `pass12345` |
| Client | `demo-clientes-client-1` (hasta `-80`) | `pass12345` |

Opciones:

```bash
# Validar el dataset completo sin conservar filas en la base de datos.
docker compose exec web python manage.py load_demo_data --dry-run

# Otra demo independiente, con usuarios y nombres propios.
docker compose exec web python manage.py load_demo_data --namespace demo-octubre --owner-email propietario-octubre@demo.com

# Fijar la fecha de referencia y elegir contrasena al crear la demo.
docker compose exec web python manage.py load_demo_data --date 2026-10-09 --password "OtraClaveDemo!"
```

`--namespace` acepta 1-13 caracteres: empieza por letra minuscula y despues
admite letras minusculas, numeros o guiones. El namespace predeterminado es
`demo-clientes`. `--date` usa la fecha local de Django por defecto.
`--fixture` permite indicar otro JSON del mismo formato.

La carga es atomica: ante un error o colision se revierte completa. Las PK se
asignan en la base de datos; las relaciones apuntan exclusivamente a objetos
nuevos del JSON. Ningun registro previo se actualiza ni elimina.

Al repetir el mismo namespace se detecta la empresa y se omite toda la carga,
sin duplicar filas ni cambiar contrasenas, fechas o ediciones hechas en la demo.
No repone datos eliminados manualmente ni aplica cambios posteriores del JSON a
una demo existente. Para una nueva presentacion con fechas actualizadas usa
otro namespace. Si existe un usuario con el mismo nombre que no corresponde a
la empresa demo, el comando falla para no apropiarse de esos datos.

Formato del JSON:

```json
{
  "version": 1,
  "records": [
    {
      "key": "owner",
      "model": "user.user",
      "fields": {
        "username": "{owner_email}",
        "email": "{owner_email}"
      }
    }
  ]
}
```

El ejemplo solo ilustra la estructura: un dataset cargable debe incluir
`owner`, `company` y el perfil owner necesario para vincular la empresa.
`{"ref":"clave"}` apunta a un registro anterior del JSON;
`{"date_offset":-30}` expresa dias respecto a la referencia;
`{"datetime_offset":1,"hour":23}` expresa dia y hora en la zona de Django.
Geometrias usan WKT con SRID 4326. No se aceptan PK, contrasenas en campos,
privilegios staff/superuser ni referencias por ID a registros existentes.

## Actualizar la actividad de una demo existente

El JSON incluye importes y cantidades variables, fechas distribuidas durante
los ultimos doce meses y 24 recogidas recientes adicionales con estados
mezclados. Las ventas varian por lote y mes para mostrar fluctuaciones en
estadisticas; las jornadas historicas incluyen completadas y canceladas.

Para aplicar estos datos a una demo que ya estaba cargada:

```bash
docker compose exec web python manage.py refresh_demo_data --dry-run
docker compose exec web python manage.py refresh_demo_data
```

`refresh_demo_data` usa el mismo JSON y namespace de `load_demo_data`.
Actualiza exclusivamente ventas, lineas, recogidas, compras, jornadas y
solicitudes de la empresa demo identificada por su owner. Conserva las cuentas,
contrasenas, empresa, clientes, flota y configuracion existentes.
Mantiene por defecto la fecha de referencia original de la demo.

Los historicos se localizan inicialmente por los datos anteriores de `lookup`
y reciben un marcador estable en notas para repetir la actualizacion sin
crear duplicados. Las nuevas recogidas recientes tambien llevan ese marcador.
Ante una coincidencia ambigua o un registro demo previo que falta, se cancela
toda la transaccion. Las ediciones operativas de esa demo se reemplazan por el
contenido del JSON al ejecutar expresamente este comando; la carga ordinaria
sigue omitiendo demos existentes.

## Elegir la cuenta del propietario

El propietario se crea con usuario y email `propietario@demo.com` y contrasena
`pass12345`. Puedes cambiar los valores al cargar:

```bash
python manage.py load_demo_data --owner-email presentacion@demo.com --password "MiClaveDemo!"
```

`--password` establece la contrasena inicial de todos los usuarios nuevos de
la demo. Al repetir una carga normal no se cambian claves existentes.
Para otra empresa demo debes elegir tambien un email de propietario distinto,
porque usuarios y emails son unicos globalmente.

Estas opciones solo se aplican a cuentas nuevas. Si la demo ya existe,
se conserva su cuenta y contrasena. Al ejecutar `refresh_demo_data` con un
propietario personalizado, indicar el mismo `--owner-email`.

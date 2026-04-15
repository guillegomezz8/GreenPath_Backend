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
- `13-sales.json` crea ventas demo con numero de factura manual y PDF regenerable desde la API o el frontend.

- `06-collections.json` ahora prioriza recogidas recientes (febrero-abril 2026), con mayoria de bidones, algunos casos pendientes/cancelados y litros confirmados coherentes para alimentar estimaciones.
- `08-truck.json` se reduce a dos furgonetas operativas de demo.
- `13-sales.json` reparte exactamente los litros confirmados y facturables cargados en `06-collections.json`, para que la demo economica mantenga coherencia entre compra y venta.

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
  apps/user/fixtures/10-route-zone-days.json
```

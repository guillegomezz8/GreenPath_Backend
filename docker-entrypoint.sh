#!/bin/sh
set -eu

# Las migraciones se ejecutan como pre-deploy en Railway. El mismo contenedor
# puede arrancar la API, un worker o beat sin efectos laterales sobre la BD.
exec "$@"

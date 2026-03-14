import logging

import requests
from django.conf import settings
from django.contrib.gis.geos import Point

from apps.base.logger import configure_logging

configure_logging()


def _build_client_geocoding_address(client):
    parts = []

    if client.address:
        parts.append(client.address.strip())
    if client.city:
        parts.append(client.city.strip())
    if client.postal_code:
        parts.append(client.postal_code.strip())
    if client.country:
        parts.append(client.country.strip())

    return ", ".join([part for part in parts if part])


def _geocode_address_with_google_maps(full_address):
    try:
        api_key = settings.GOOGLE_MAPS_API_KEY
        if not api_key:
            logging.warning("[user_utils - _geocode_address_with_google_maps] GOOGLE_MAPS_API_KEY no configurada")
            return None

        if not full_address:
            logging.warning("[user_utils - _geocode_address_with_google_maps] Direccion vacia para geocodificar")
            return None

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": full_address,
                "key": api_key,
                "region": "es",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        status = payload.get("status")
        if status != "OK":
            error_message = payload.get("error_message", "")
            logging.warning(f"[user_utils - _geocode_address_with_google_maps] Geocodificacion sin resultado para direccion '{full_address}': status={status}, error={error_message}")
            return None

        results = payload.get("results", [])
        if not results:
            logging.warning(f"[user_utils - _geocode_address_with_google_maps] Geocodificacion sin resultados para direccion '{full_address}'")
            return None

        geometry = results[0].get("geometry", {})
        location = geometry.get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")

        if lat is None or lng is None:
            logging.warning(f"[user_utils - _geocode_address_with_google_maps] Respuesta de geocodificacion invalida para direccion '{full_address}'")
            return None

        return Point(float(lng), float(lat), srid=4326)
    except Exception as e:
        logging.error(f"[user_utils - _geocode_address_with_google_maps] Error geocodificando direccion '{full_address}': {str(e)}")
        return None


def sync_client_location_from_address(client, clear_on_failure=False):
    try:
        full_address = _build_client_geocoding_address(client)
        point = _geocode_address_with_google_maps(full_address)

        if point:
            client.location = point
            client.save(update_fields=["location"])
            logging.info(f"[user_utils - sync_client_location_from_address] Location actualizada para cliente {client.id} desde direccion '{full_address}'")
            return True

        if clear_on_failure:
            client.location = None
            client.save(update_fields=["location"])
            logging.warning(f"[user_utils - sync_client_location_from_address] Location limpiada para cliente {client.id} por fallo de geocodificacion")
        else:
            logging.warning(f"[user_utils - sync_client_location_from_address] Location no actualizada para cliente {client.id} por fallo de geocodificacion")
        return False
    except Exception as e:
        logging.error(f"[user_utils - sync_client_location_from_address] Error actualizando location para cliente {client.id}: {str(e)}")
        return False

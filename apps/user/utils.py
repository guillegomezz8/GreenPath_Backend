import logging

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.text import slugify

from apps.base.logger import configure_logging
from apps.user.models.user import User

configure_logging()

AUTO_CLIENT_EMAIL_DOMAIN = "clients.greenpath.local"


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


def _normalize_client_identifier_base(value, fallback="cliente"):
    normalized_value = slugify((value or "").strip()).strip("-")
    return normalized_value or fallback


def _build_unique_value(base_value, max_length, exists_callback):
    safe_base = (base_value or "")[:max_length] or "cliente"
    candidate = safe_base
    counter = 2

    while exists_callback(candidate):
        suffix = f"-{counter}"
        truncated_base = safe_base[: max_length - len(suffix)] or safe_base[:max_length]
        candidate = f"{truncated_base}{suffix}"
        counter += 1

    return candidate


def build_client_username_seed(name):
    return _normalize_client_identifier_base(name, fallback="cliente")


def build_unique_client_username(name):
    base_username = build_client_username_seed(name)
    return _build_unique_value(
        base_value=base_username,
        max_length=255,
        exists_callback=lambda candidate: User.objects.filter(username=candidate).exists(),
    )


def build_unique_client_placeholder_email(name):
    local_part_base = _normalize_client_identifier_base(name, fallback="cliente")
    unique_local_part = _build_unique_value(
        base_value=local_part_base,
        max_length=64,
        exists_callback=lambda candidate: User.objects.filter(
            email__iexact=f"{candidate}@{AUTO_CLIENT_EMAIL_DOMAIN}"
        ).exists(),
    )
    return f"{unique_local_part}@{AUTO_CLIENT_EMAIL_DOMAIN}"


def resolve_client_user_credentials(name, username="", email=""):
    cleaned_name = (name or "").strip()
    cleaned_username = (username or "").strip()
    cleaned_email = (email or "").strip().lower()

    resolved_username = cleaned_username or build_unique_client_username(cleaned_name)
    resolved_email = cleaned_email or build_unique_client_placeholder_email(cleaned_name or resolved_username)
    return resolved_username, resolved_email


def is_auto_generated_client_email(email):
    cleaned_email = (email or "").strip().lower()
    return cleaned_email.endswith(f"@{AUTO_CLIENT_EMAIL_DOMAIN}")


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

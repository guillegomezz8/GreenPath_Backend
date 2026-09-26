import logging

from apps.base.logger import configure_logging
from apps.company.models import CompanySettings

configure_logging()


def resolve_user_company(user):
    try:
        if user.role_type == "owner" and hasattr(user, "worker_profile") and user.worker_profile.company_id:
            return user.worker_profile.company
        if user.role_type == "owner":
            return user.companies.order_by("id").first()
        if user.role_type == "worker" and hasattr(user, "worker_profile") and user.worker_profile.company_id:
            return user.worker_profile.company
        return None
    except Exception as e:
        logging.warning(f"[company_utils - resolve_user_company] No se pudo resolver la empresa del usuario {user.id}: {str(e)}")
        return None


def get_or_create_company_settings(company):
    settings_obj, _ = CompanySettings.objects.get_or_create(company=company)
    return settings_obj


def get_user_company_features(user):
    defaults = {
        "collections_enabled": False,
        "bulk_collections_enabled": False,
    }
    if not getattr(user, "is_authenticated", False):
        return defaults

    company = resolve_user_company(user)
    if company:
        settings_obj = get_or_create_company_settings(company)
        return {
            "collections_enabled": settings_obj.collections_enabled,
            "bulk_collections_enabled": settings_obj.bulk_collections_enabled,
        }

    if user.is_staff or user.is_superuser:
        return {key: True for key in defaults}

    if user.role_type == "client" and hasattr(user, "client_profile"):
        return {
            "collections_enabled": any(
                get_or_create_company_settings(company).collections_enabled
                for company in user.client_profile.companies.all()
            ),
            "bulk_collections_enabled": False,
        }
    return defaults


def resolve_default_collection_price_per_liter(company=None, client=None, worker=None, route_day_client=None):
    try:
        resolved_company = company

        if resolved_company is None and route_day_client is not None:
            resolved_company = route_day_client.route_day.route.company
        if resolved_company is None and worker is not None and worker.company_id:
            resolved_company = worker.company
        if resolved_company is None and client is not None:
            resolved_company = client.companies.order_by("id").first()

        if resolved_company is None:
            logging.info("[company_utils - resolve_default_collection_price_per_liter] No se encontro empresa para resolver precio global")
            return None

        settings_obj = get_or_create_company_settings(resolved_company)
        return settings_obj.default_price_per_liter
    except Exception as e:
        logging.warning(f"[company_utils - resolve_default_collection_price_per_liter] No se pudo resolver el precio global: {str(e)}")
        return None

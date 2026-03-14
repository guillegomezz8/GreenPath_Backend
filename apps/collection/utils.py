from apps.base.enums import ContainerType

from decimal import Decimal
import logging

def container_capacity_liters(container_type):
    try:
        if container_type == ContainerType.BIDONES:
            return Decimal("60")
        return Decimal("1000")
    except Exception as e:
        logging.error(f"[collection_utils - container_capacity_liters] Error calculando capacidad para tipo {container_type}: {str(e)}")
        raise

from apps.base.enums import ContainerType

from decimal import Decimal

def container_capacity_liters(container_type):
    if container_type == ContainerType.BIDONES:
        return Decimal("60")
    return Decimal("1000")
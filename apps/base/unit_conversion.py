from decimal import Decimal

from apps.base.enums import QuantityUnit
from apps.base.literals import OIL_DENSITY_POSITIVE

OUTPUT_STEP = Decimal("0.0001")

UNIT_ALIASES = {
    "L": QuantityUnit.LITER,
    "LT": QuantityUnit.LITER,
    "LTS": QuantityUnit.LITER,
    "LITRO": QuantityUnit.LITER,
    "LITROS": QuantityUnit.LITER,
    "KG": QuantityUnit.KILOGRAM,
    "KGS": QuantityUnit.KILOGRAM,
    "KILO": QuantityUnit.KILOGRAM,
    "KILOS": QuantityUnit.KILOGRAM,
    "KILOGRAMO": QuantityUnit.KILOGRAM,
    "KILOGRAMOS": QuantityUnit.KILOGRAM,
    "UD": QuantityUnit.UNIT,
    "UDS": QuantityUnit.UNIT,
    "UNIDAD": QuantityUnit.UNIT,
    "UNIDADES": QuantityUnit.UNIT,
}


def normalize_quantity_unit(value):
    normalized = str(value or "").strip().upper().replace(".", "")
    return UNIT_ALIASES.get(normalized)


class QuantityConverter:
    def __init__(self, density_kg_per_liter):
        self.density = Decimal(density_kg_per_liter)
        if self.density <= 0:
            raise ValueError(OIL_DENSITY_POSITIVE)

    def to_liters(self, quantity, unit):
        value = Decimal(quantity or 0)
        normalized_unit = normalize_quantity_unit(unit)
        if normalized_unit == QuantityUnit.LITER:
            return value
        if normalized_unit == QuantityUnit.KILOGRAM:
            return value / self.density
        return None

    def from_liters(self, liters):
        value = Decimal(liters or 0)
        return {
            QuantityUnit.LITER: value.quantize(OUTPUT_STEP),
            QuantityUnit.KILOGRAM: (value * self.density).quantize(OUTPUT_STEP),
        }

    def aggregate_as_liters(self, rows):
        total = Decimal("0.00")
        ignored = 0
        for row in rows:
            converted = self.to_liters(row.get("quantity"), row.get("unit"))
            if converted is None:
                ignored += 1
                continue
            total += converted
        return total, ignored

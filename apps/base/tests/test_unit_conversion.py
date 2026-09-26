from decimal import Decimal

from django.test import SimpleTestCase

from apps.base.unit_conversion import QuantityConverter, normalize_quantity_unit


class QuantityConverterTests(SimpleTestCase):
    def setUp(self):
        self.converter = QuantityConverter(Decimal("0.9200"))

    def test_normalizes_common_unit_aliases(self):
        self.assertEqual(normalize_quantity_unit("litros"), "L")
        self.assertEqual(normalize_quantity_unit("kg"), "KG")
        self.assertEqual(normalize_quantity_unit("uds."), "UD")

    def test_converts_liters_and_kilograms(self):
        self.assertEqual(self.converter.to_liters(Decimal("92"), "KG"), Decimal("100"))
        equivalents = self.converter.from_liters(Decimal("100"))
        self.assertEqual(equivalents["KG"], Decimal("92.0000"))

    def test_units_are_not_converted_to_physical_volume(self):
        self.assertIsNone(self.converter.to_liters(Decimal("5"), "UD"))

    def test_unsupported_units_are_reported_as_ignored(self):
        total, ignored = self.converter.aggregate_as_liters([
            {"quantity": Decimal("10"), "unit": "L"},
            {"quantity": Decimal("2"), "unit": "cajas"},
        ])
        self.assertEqual(total, Decimal("10"))
        self.assertEqual(ignored, 1)

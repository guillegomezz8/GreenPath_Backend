from rest_framework import serializers

from apps.base.enums import BulkCollectionCalculationMode, QuantityUnit
from apps.bulk_collection.models import BulkCollection
from apps.base.literals import BULK_COLLECTION_CALCULATION_VALUE_REQUIRED, BULK_COLLECTION_INTEGER_UNITS_REQUIRED, BULK_COLLECTION_INVOICE_TOO_LARGE, BULK_COLLECTION_INVOICE_TYPE_INVALID

CALCULATION_INPUTS = {
    BulkCollectionCalculationMode.TOTAL: ("quantity", "unit_price"),
    BulkCollectionCalculationMode.UNIT_PRICE: ("quantity", "total_price"),
    BulkCollectionCalculationMode.QUANTITY: ("unit_price", "total_price"),
}
CALCULATION_FIELDS = ("quantity", "unit_price", "total_price")
MAX_INVOICE_SIZE = 10 * 1024 * 1024
ALLOWED_INVOICE_TYPES = {"application/pdf", "image/jpeg", "image/png"}


class BulkCollectionSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    client_tax_id = serializers.CharField(source="client.cif", read_only=True)
    unit_label = serializers.CharField(source="get_unit_display", read_only=True)
    calculation_mode_label = serializers.CharField(source="get_calculation_mode_display", read_only=True)

    class Meta:
        model = BulkCollection
        fields = (
            "id", "company", "client", "client_name", "client_tax_id",
            "collection_date", "invoice_file", "unit", "unit_label",
            "calculation_mode", "calculation_mode_label", "quantity",
            "unit_price", "total_price", "billable", "notes",
            "created_date", "modified_date",
        )
        read_only_fields = ("id", "company", "created_date", "modified_date")
        extra_kwargs = {
            "quantity": {"required": False},
            "unit_price": {"required": False},
            "total_price": {"required": False},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and hasattr(user, "worker_profile"):
            self.fields["client"].queryset = self.fields["client"].queryset.filter(
                companies=user.worker_profile.company
            ).distinct()

    def validate(self, attrs):
        mode = attrs.get("calculation_mode", getattr(self.instance, "calculation_mode", BulkCollectionCalculationMode.TOTAL))
        values = {field: attrs.get(field, getattr(self.instance, field, None)) for field in CALCULATION_FIELDS}
        errors = {
            field: BULK_COLLECTION_CALCULATION_VALUE_REQUIRED
            for field in CALCULATION_INPUTS[mode]
            if values[field] is None or values[field] <= 0
        }
        if errors:
            raise serializers.ValidationError(errors)

        unit = attrs.get("unit", getattr(self.instance, "unit", None))
        quantity = self._resolved_quantity(mode, values)
        if unit == QuantityUnit.UNIT and quantity % 1 != 0:
            raise serializers.ValidationError({"quantity": BULK_COLLECTION_INTEGER_UNITS_REQUIRED})
        return attrs

    @staticmethod
    def _resolved_quantity(mode, values):
        if mode == BulkCollectionCalculationMode.QUANTITY:
            return values["total_price"] / values["unit_price"]
        return values["quantity"]

    def validate_invoice_file(self, value):
        if not value:
            return value
        if value.size > MAX_INVOICE_SIZE:
            raise serializers.ValidationError(BULK_COLLECTION_INVOICE_TOO_LARGE)
        content_type = getattr(value, "content_type", None)
        if content_type and content_type not in ALLOWED_INVOICE_TYPES:
            raise serializers.ValidationError(BULK_COLLECTION_INVOICE_TYPE_INVALID)
        return value

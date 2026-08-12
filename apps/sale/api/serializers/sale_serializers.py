import logging

from django.db import transaction
from rest_framework import serializers

from apps.base.logger import configure_logging
from apps.sale.models import Sale, SaleLine

configure_logging()


class SaleLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleLine
        fields = (
            "id",
            "position",
            "product_description",
            "quantity",
            "unit",
            "unit_price",
            "tax_rate",
            "subtotal",
            "tax_amount",
            "total",
        )
        read_only_fields = ("id", "position", "subtotal", "tax_amount", "total")


class SaleSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.fiscal_name", read_only=True)
    buyer_tax_id = serializers.CharField(source="buyer.tax_id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    lines = SaleLineSerializer(many=True, read_only=True)
    line_count = serializers.IntegerField(source="lines.count", read_only=True)

    class Meta:
        model = Sale
        exclude = (
            "created_date",
            "modified_date",
            "deleted_date",
            "sale_date",
            "invoice_issuer",
            "invoice_pdf",
            "invoice_generated_at",
        )


class SaleBaseWriteSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(required=True, allow_blank=False)
    lines = SaleLineSerializer(many=True, required=False, allow_empty=False)

    class Meta:
        model = Sale
        fields = (
            "buyer",
            "invoice_number",
            "invoice_date",
            "product_description",
            "quantity",
            "unit",
            "unit_price",
            "tax_rate",
            "currency",
            "notes",
            "lines",
        )
        extra_kwargs = {
            "product_description": {"required": False},
            "quantity": {"required": False},
            "unit": {"required": False},
            "unit_price": {"required": False},
            "tax_rate": {"required": False},
        }

    legacy_line_fields = (
        "product_description",
        "quantity",
        "unit",
        "unit_price",
        "tax_rate",
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if "lines" in attrs:
            return attrs

        if self.instance is None:
            missing = [
                field
                for field in ("product_description", "quantity", "unit_price")
                if field not in attrs
            ]
            if missing:
                raise serializers.ValidationError(
                    {"lines": "Debes indicar al menos una linea de factura."}
                )
        return attrs

    def validate_buyer(self, value):
        company = self.context["company"]
        if value.company_id != company.id:
            logging.error(f"[sale_serializers - validate_buyer] Comprador {value.id} fuera de empresa {company.id}")
            raise serializers.ValidationError("El comprador no pertenece a tu empresa.")
        return value

    def validate_invoice_date(self, value):
        if not value:
            raise serializers.ValidationError("La fecha de factura es obligatoria.")
        return value

    def validate_invoice_number(self, value):
        cleaned_value = (value or "").strip()
        if not cleaned_value:
            raise serializers.ValidationError("El numero de factura es obligatorio.")

        company = self.context["company"]
        queryset = Sale.objects.filter(company=company, invoice_number__iexact=cleaned_value)
        instance = self.instance
        if instance and instance.id:
            queryset = queryset.exclude(id=instance.id)
        if queryset.exists():
            logging.error(f"[sale_serializers - validate_invoice_number] Numero de factura duplicado {cleaned_value} en empresa {company.id}")
            raise serializers.ValidationError("Ya existe una venta con ese numero de factura.")
        return cleaned_value

    def _legacy_line_data(self, validated_data, instance=None):
        values = {}
        for field in self.legacy_line_fields:
            if field in validated_data:
                values[field] = validated_data[field]
            elif instance is not None:
                values[field] = getattr(instance, field)

        values.setdefault("unit", "L")
        values.setdefault("tax_rate", "21.00")
        return values

    def _prepare_sale_data(self, validated_data, lines_data):
        if not lines_data:
            return
        first_line = lines_data[0]
        for field in self.legacy_line_fields:
            validated_data[field] = first_line[field]

    def _replace_lines(self, sale, lines_data):
        sale.lines.all().delete()
        for position, line_data in enumerate(lines_data):
            line = SaleLine(
                sale=sale,
                position=position,
                **line_data,
            )
            line.save(recalculate_sale=False)
        sale.recalculate_from_lines()


class CreateSaleSerializer(SaleBaseWriteSerializer):
    def create(self, validated_data):
        try:
            with transaction.atomic():
                company = self.context["company"]
                lines_data = validated_data.pop("lines", None)
                if lines_data is None:
                    lines_data = [self._legacy_line_data(validated_data)]
                self._prepare_sale_data(validated_data, lines_data)

                sale = Sale(company=company, **validated_data)
                sale.save()
                self._replace_lines(sale, lines_data)
                return sale
        except Exception as e:
            logging.error(f"[sale_serializers - create] Error creando venta: {str(e)}")
            raise serializers.ValidationError(f"Error creando venta: {str(e)}")


class UpdateSaleSerializer(SaleBaseWriteSerializer):
    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                lines_data = validated_data.pop("lines", None)
                legacy_fields_supplied = any(
                    field in validated_data for field in self.legacy_line_fields
                )
                if lines_data is not None:
                    self._prepare_sale_data(validated_data, lines_data)

                for attr, value in validated_data.items():
                    setattr(instance, attr, value)
                instance.save()

                if lines_data is not None:
                    self._replace_lines(instance, lines_data)
                elif legacy_fields_supplied:
                    self._replace_lines(
                        instance,
                        [self._legacy_line_data(validated_data, instance)],
                    )
                return instance
        except Exception as e:
            logging.error(f"[sale_serializers - update] Error actualizando venta {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando venta: {str(e)}")


class PartialUpdateSaleSerializer(UpdateSaleSerializer):
    class Meta(UpdateSaleSerializer.Meta):
        extra_kwargs = {field: {"required": False} for field in UpdateSaleSerializer.Meta.fields}

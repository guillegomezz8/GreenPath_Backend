import logging

from rest_framework import serializers

from apps.base.logger import configure_logging
from apps.sale.models import Sale
from apps.sale.utils import generate_sale_invoice_pdf

configure_logging()


class SaleSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source="buyer.fiscal_name", read_only=True)
    buyer_tax_id = serializers.CharField(source="buyer.tax_id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    invoice_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        exclude = ("created_date", "modified_date", "deleted_date", "sale_date")

    def get_invoice_pdf_url(self, obj):
        if not obj.invoice_pdf:
            return None
        request = self.context.get("request")
        url = obj.invoice_pdf.url
        return request.build_absolute_uri(url) if request else url


class SaleBaseWriteSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(required=True, allow_blank=False)

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
        )

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


class CreateSaleSerializer(SaleBaseWriteSerializer):
    def create(self, validated_data):
        try:
            company = self.context["company"]
            sale = Sale(company=company, **validated_data)
            sale.save()
            generate_sale_invoice_pdf(sale)
            return sale
        except Exception as e:
            logging.error(f"[sale_serializers - create] Error creando venta: {str(e)}")
            raise serializers.ValidationError(f"Error creando venta: {str(e)}")


class UpdateSaleSerializer(SaleBaseWriteSerializer):
    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            generate_sale_invoice_pdf(instance)
            return instance
        except Exception as e:
            logging.error(f"[sale_serializers - update] Error actualizando venta {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando venta: {str(e)}")


class PartialUpdateSaleSerializer(UpdateSaleSerializer):
    class Meta(UpdateSaleSerializer.Meta):
        extra_kwargs = {field: {"required": False} for field in UpdateSaleSerializer.Meta.fields}

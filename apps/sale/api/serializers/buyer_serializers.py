import logging

from rest_framework import serializers

from apps.base.logger import configure_logging
from apps.sale.models import Buyer

configure_logging()


class BuyerSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    full_fiscal_address = serializers.CharField(read_only=True)

    class Meta:
        model = Buyer
        exclude = ("created_date", "modified_date", "deleted_date")


class CreateBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = (
            "fiscal_name",
            "tax_id",
            "fiscal_address",
            "postal_code",
            "city",
            "province",
            "country",
            "email",
            "phone",
            "contact_person",
            "notes",
        )

    def create(self, validated_data):
        try:
            company = self.context["company"]
            return Buyer.objects.create(company=company, **validated_data)
        except Exception as e:
            logging.error(f"[buyer_serializers - create] Error creando comprador: {str(e)}")
            raise serializers.ValidationError(f"Error creando comprador: {str(e)}")


class UpdateBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = (
            "fiscal_name",
            "tax_id",
            "fiscal_address",
            "postal_code",
            "city",
            "province",
            "country",
            "email",
            "phone",
            "contact_person",
            "notes",
        )

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"[buyer_serializers - update] Error actualizando comprador {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando comprador: {str(e)}")


class PartialUpdateBuyerSerializer(UpdateBuyerSerializer):
    class Meta(UpdateBuyerSerializer.Meta):
        extra_kwargs = {field: {"required": False} for field in UpdateBuyerSerializer.Meta.fields}

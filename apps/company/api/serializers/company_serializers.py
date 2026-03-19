from rest_framework import serializers
from django.contrib.gis.geos import Point
from apps.company.models import Company, CompanyHub, CompanySettings
import logging
from apps.base.logger import configure_logging

configure_logging()


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        exclude = ('modified_date', 'deleted_date', 'created_date')


class CreateCompanySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    cif = serializers.CharField(required=True)
    logo = serializers.ImageField(required=False)

    class Meta:
        model = Company
        fields = ('name', 'address', 'phone', 'email', 'cif', 'logo')     


class UpdateCompanySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    cif = serializers.CharField(required=True)
    logo = serializers.ImageField(required=True)

    class Meta:
        model = Company
        fields = ('name', 'address', 'phone', 'email', 'cif', 'logo')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"[company_serializers - update] Error updating company with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating company: {str(e)}")


class PartialUpdateCompanySerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    cif = serializers.CharField(required=False)
    logo = serializers.ImageField(required=False)

    class Meta:
        model = Company
        fields = ('name', 'address', 'phone', 'email', 'cif', 'logo')

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"[company_serializers - update] Error updating company with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating company: {str(e)}")


class CompanySettingsSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    hub = serializers.SerializerMethodField(read_only=True)
    hub_name = serializers.CharField(required=False, allow_blank=True, write_only=True)
    hub_lat = serializers.FloatField(required=False, allow_null=True, write_only=True)
    hub_lng = serializers.FloatField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = CompanySettings
        fields = (
            "company_id",
            "company_name",
            "default_price_per_liter",
            "billing_business_name",
            "billing_tax_id",
            "billing_address",
            "billing_postal_code",
            "billing_city",
            "billing_province",
            "billing_country",
            "billing_phone",
            "billing_email",
            "billing_bank_account",
            "billing_ler_code",
            "billing_footer",
            "hub",
            "hub_name",
            "hub_lat",
            "hub_lng",
        )

    def get_hub(self, obj):
        if not hasattr(obj.company, "hub") or not obj.company.hub:
            return None

        hub = obj.company.hub
        return {
            "id": hub.id,
            "name": hub.name,
            "location": {
                "lat": hub.location.y,
                "lng": hub.location.x,
            } if hub.location else None,
        }

    def validate(self, attrs):
        initial_data = self.initial_data
        hub_lat_in_request = "hub_lat" in initial_data
        hub_lng_in_request = "hub_lng" in initial_data

        if hub_lat_in_request != hub_lng_in_request:
            logging.error("[company_serializers - validate] Debes indicar latitud y longitud del hub")
            raise serializers.ValidationError("Debes indicar latitud y longitud del hub.")

        return attrs

    def update(self, instance, validated_data):
        try:
            initial_data = self.initial_data
            hub_name_in_request = "hub_name" in initial_data
            hub_lat_in_request = "hub_lat" in initial_data
            hub_lng_in_request = "hub_lng" in initial_data

            hub_name = validated_data.pop("hub_name", "") if hub_name_in_request else ""
            hub_lat = validated_data.pop("hub_lat", None) if hub_lat_in_request else None
            hub_lng = validated_data.pop("hub_lng", None) if hub_lng_in_request else None

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if hub_name_in_request or hub_lat_in_request or hub_lng_in_request:
                existing_hub = instance.company.hub if hasattr(instance.company, "hub") and instance.company.hub else None
                default_hub_name = existing_hub.name if existing_hub and existing_hub.name else f"Nave {instance.company.name}"

                hub, _ = CompanyHub.objects.get_or_create(
                    company=instance.company,
                    defaults={"name": default_hub_name},
                )

                if hub_name_in_request:
                    hub.name = hub_name.strip() if hub_name.strip() else default_hub_name

                if hub_lat_in_request and hub_lng_in_request:
                    if hub_lat is None and hub_lng is None:
                        hub.location = None
                    else:
                        hub.location = Point(float(hub_lng), float(hub_lat), srid=4326)

                if not hub.name:
                    hub.name = default_hub_name

                hub.save()

            return instance
        except Exception as e:
            logging.error(f"[company_serializers - update] Error actualizando configuracion de empresa {instance.company_id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando configuracion: {str(e)}")

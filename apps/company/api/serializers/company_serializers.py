from rest_framework import serializers
from apps.company.models import Company
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
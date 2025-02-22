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

    class Meta:
        model = Company
        fields = ('name', 'address', 'phone', 'email', 'cif', 'logo')

    def create(self, validated_data):
        try:
            company = Company.objects.create(**validated_data)
            return company
        except Exception as e:
            logging.error(f"Error creating company: {str(e)}")
            raise serializers.ValidationError(f"Error creating company: {str(e)}")


class UpdateCompanySerializer(serializers.ModelSerializer):

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
            logging.error(f"Error updating company with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating company: {str(e)}")


class PartialUpdateCompanySerializer(serializers.ModelSerializer):

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
            logging.error(f"Error updating company with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating company: {str(e)}")

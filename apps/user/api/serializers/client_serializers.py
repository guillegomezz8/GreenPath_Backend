from rest_framework import serializers
from apps.company.models import Company
import logging
from apps.base.logger import configure_logging
from apps.user.models.client import Client

configure_logging()

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        exclude = ('modified_date', 'deleted_date', 'created_date')

class CreateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    adress = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)
    
    class Meta:
        model = Client
        fields = ('user', 'companies', 'name', 'adress', 'phone', 'cif')
    
    def create(self, validated_data):
        try:
            companies = validated_data.pop('companies', None)
            client = Client.objects.create(**validated_data)
            
            if companies:
                client.companies.set(companies)
                
            return client
        except Exception as e:
            logging.error(f"Error creating client: {str(e)}")
            raise serializers.ValidationError(f"Error creating client: {str(e)}")

class UpdateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    adress = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)
    
    class Meta:
        model = Client
        fields = ('companies', 'name', 'adress', 'phone', 'cif')
    
    def update(self, instance, validated_data):
        try:
            companies = validated_data.pop('companies', None)
            
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            if companies is not None:
                instance.companies.set(companies)
                
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating client: {str(e)}")

class PartialUpdateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    adress = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    cif = serializers.CharField(required=False)
    
    class Meta:
        model = Client
        fields = ('companies', 'name', 'adress', 'phone', 'cif')
    
    def update(self, instance, validated_data):
        try:
            companies = validated_data.pop('companies', None)
            
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            if companies is not None:
                instance.companies.set(companies)
                
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating client: {str(e)}")
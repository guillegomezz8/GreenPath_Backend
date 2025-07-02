from rest_framework import serializers
from apps.company.models import Company
import logging
from django.contrib.gis.geos import GEOSGeometry
from apps.base.logger import configure_logging
from apps.user.models.client import Client

configure_logging()

class ClientSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Client
        exclude = ('modified_date', 'deleted_date', 'created_date')

class CreateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)
    
    class Meta:
        model = Client
        fields = ('user', 'companies', 'name', 'address', 'phone', 'cif')
    
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
    email = serializers.EmailField(source='user.email', required=False)
    address = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    cif = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    location = serializers.CharField(required=True)
    
    class Meta:
        model = Client
        fields = ('name', 'email', 'address', 'phone', 'cif', 'city', 'postal_code', 'country', 'location')

    def update(self, instance, validated_data):
        try:
            user_data = validated_data.pop('user', {})
            email = user_data.get('email')            
            location_wkt = validated_data.pop('location', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if location_wkt:
                try:
                    instance.location = GEOSGeometry(location_wkt)
                except Exception as geo_error:
                    raise serializers.ValidationError({"location": f"Ubicación inválida: {geo_error}"})

            instance.save()

            if email and hasattr(instance, 'user'):
                instance.user.email = email
                instance.user.save()

            return instance

        except Exception as e:
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")

class PartialUpdateClientSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    email = serializers.EmailField(source='user.email', required=False)
    address = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    cif = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    location = serializers.CharField(required=True)

    class Meta:
        model = Client
        fields = ('name',  'email', 'address', 'phone', 'cif', 'city', 'postal_code', 'country', 'location')
    
    def update(self, instance, validated_data):
        try:
            user_data = validated_data.pop('user', {})
            email = user_data.get('email')            
            location_wkt = validated_data.pop('location', None)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if location_wkt:
                try:
                    instance.location = GEOSGeometry(location_wkt)
                except Exception as geo_error:
                    raise serializers.ValidationError({"location": f"Ubicación inválida: {geo_error}"})

            instance.save()

            if email and hasattr(instance, 'user'):
                instance.user.email = email
                instance.user.save()

            return instance

        except Exception as e:
            logging.error(f"Error updating client with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error actualizando cliente: {str(e)}")
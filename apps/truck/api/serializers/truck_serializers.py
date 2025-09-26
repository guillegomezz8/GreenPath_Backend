from rest_framework import serializers
from apps.truck.models import Truck
from apps.company.models import Company
from apps.user.models.user import User
from apps.base.enums import TruckStatus, Fuel
import logging
from apps.base.logger import configure_logging

configure_logging()


class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        exclude = ("modified_date", "deleted_date", "created_date")


class CreateTruckSerializer(serializers.ModelSerializer):
    registration_number = serializers.CharField(required=True)
    brand = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    model = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    year = serializers.IntegerField(required=False, allow_null=True)
    capacity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    status = serializers.ChoiceField(choices=TruckStatus.choices, required=False)
    fuel = serializers.ChoiceField(choices=Fuel.choices, required=False, allow_null=True)
    driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Truck
        fields = ("registration_number", "brand", "model", "year", "capacity", "status", "fuel", "driver", "company")


class UpdateTruckSerializer(serializers.ModelSerializer):
    registration_number = serializers.CharField(required=True)
    brand = serializers.CharField(required=True, allow_blank=True)
    model = serializers.CharField(required=True, allow_blank=True)
    year = serializers.IntegerField(required=True, allow_null=True)
    capacity = serializers.DecimalField(max_digits=10, decimal_places=2, required=True, allow_null=True)
    status = serializers.ChoiceField(choices=TruckStatus.choices, required=True)
    fuel = serializers.ChoiceField(choices=Fuel.choices, required=True, allow_null=True)
    driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True, allow_null=True)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=True, allow_null=True)

    class Meta:
        model = Truck
        fields = ("registration_number", "brand", "model", "year", "capacity", "status", "fuel", "driver", "company")

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating truck with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating truck: {str(e)}")


class PartialUpdateTruckSerializer(serializers.ModelSerializer):
    registration_number = serializers.CharField(required=False)
    brand = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    model = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    year = serializers.IntegerField(required=False, allow_null=True)
    capacity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    status = serializers.ChoiceField(choices=TruckStatus.choices, required=False)
    fuel = serializers.ChoiceField(choices=Fuel.choices, required=False, allow_null=True)
    driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Truck
        fields = ("registration_number", "brand", "model", "year", "capacity", "status", "fuel", "driver", "company")

    def update(self, instance, validated_data):
        try:
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            return instance
        except Exception as e:
            logging.error(f"Error updating truck with id {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error updating truck: {str(e)}")

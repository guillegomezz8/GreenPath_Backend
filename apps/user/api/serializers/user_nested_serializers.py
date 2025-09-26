from rest_framework import serializers

from apps.user.models.user import User


class UserNestedWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")
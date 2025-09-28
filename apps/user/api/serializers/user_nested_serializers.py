from rest_framework import serializers

from apps.user.models.user import User


class UserNestedWriteSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, trim_whitespace=True)
    email = serializers.EmailField(max_length=255)

    class Meta:
        model = User
        fields = ("username", "email")
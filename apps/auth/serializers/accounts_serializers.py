from rest_framework import serializers


class GoogleCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

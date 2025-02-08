from django.contrib.auth import authenticate

from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.base.literals import ERROR, INCORRECT_CREDENTIALS, MESSAGE, SUCCESSFULL_LOGOUT, USER_DOESNT_EXISTS
from apps.user.api.serializers.user_serializers import (
    CustomUserSerializer
)
from apps.user.api.serializers.authentication_serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer
)
from .models import User


class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        username = request.data.get('username', '')
        password = request.data.get('password', '')
        user = authenticate(
            username=username,
            password=password
        )

        if user:
            login_serializer = self.serializer_class(data=request.data)
            if login_serializer.is_valid():
                user_serializer = CustomUserSerializer(user)
                return Response({
                    'token': login_serializer.validated_data.get('access'),
                    'refresh-token': login_serializer.validated_data.get('refresh'),
                    'user': user_serializer.data,
                    'message': 'Login successfully'
                }, status=status.HTTP_200_OK)
            return Response({ERROR: INCORRECT_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)
        return Response({ERROR: INCORRECT_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)


class Logout(GenericAPIView):
    serializer_class = LogoutSerializer
    
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(id=request.data.get('user', 0))
        if user.exists():
            RefreshToken.for_user(user.first())
            return Response({MESSAGE: SUCCESSFULL_LOGOUT}, status=status.HTTP_200_OK)
        return Response({ERROR: USER_DOESNT_EXISTS}, status=status.HTTP_400_BAD_REQUEST)
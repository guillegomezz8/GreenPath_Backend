import logging

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.base.literals import (
    DETAILS,
    ERROR,
    INCORRECT_CREDENTIALS,
    INTERNAL_ERROR,
    MESSAGE,
    SUCCESSFULL_LOGIN,
    SUCCESSFULL_LOGOUT,
    USER_DOESNT_EXISTS,
)
from apps.base.logger import configure_logging
from apps.user.api.serializers.authentication_serializers import (
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
)
from apps.user.api.serializers.user_serializers import CustomUserSerializer
from apps.user.models.user import User

configure_logging()


class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            logging.info(f"[user_views - post] Inicio de sesion para el usuario: {request.data.get('username', 'Desconocido')}")
            username = request.data.get("username", "")
            password = request.data.get("password", "")
            user = authenticate(username=username, password=password)

            if user:
                login_serializer = self.serializer_class(data=request.data)
                if login_serializer.is_valid():
                    user_serializer = CustomUserSerializer(user)
                    return Response(
                        {
                            "token": login_serializer.validated_data.get("access"),
                            "refresh-token": login_serializer.validated_data.get("refresh"),
                            "user": user_serializer.data,
                            MESSAGE: SUCCESSFULL_LOGIN,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response({ERROR: INCORRECT_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)
            return Response({ERROR: INCORRECT_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f"[user_views - post] Error en login: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Logout(GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        try:
            logging.info(f"[user_views - post] Cierre de sesion para el usuario ID: {request.data.get('user', 'Desconocido')}")
            user = User.objects.filter(id=request.data.get("user", 0))
            if user.exists():
                RefreshToken.for_user(user.first())
                return Response({MESSAGE: SUCCESSFULL_LOGOUT}, status=status.HTTP_200_OK)
            return Response({ERROR: USER_DOESNT_EXISTS}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f"[user_views - post] Error en logout: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

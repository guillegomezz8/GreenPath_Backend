# apps/auth/api/views_google.py
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from apps.user.models.user import User
from apps.base.literals import ERROR, USER_NOT_FOUND, INVALID_EMAIL_RECEIVED, INVALID_GOOGLE_ID_TOKEN, INTERNAL_ERROR

class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        try:
            credential = request.data.get("credential") or request.data.get("token")
            
            if not credential:
                return Response({ERROR: "credential o token requerido"}, status=status.HTTP_400_BAD_REQUEST)

            idinfo = None
            client_ids = getattr(settings, "GOOGLE_CLIENT_ID", "").split(",")
            errors = []
            
            for aud in [c.strip() for c in client_ids if c.strip()]:
                try:
                    idinfo = id_token.verify_oauth2_token(
                        credential, google_requests.Request(), aud
                    )
                    break
                except Exception as e:
                    errors.append(str(e))
                    
            if not idinfo:
                logging.error(f"Google ID token inválido: {errors}")
                return Response({ERROR: INVALID_GOOGLE_ID_TOKEN}, status=status.HTTP_401_UNAUTHORIZED)

            email = idinfo.get("email")
            if not email or not idinfo.get("email_verified"):
                return Response({ERROR: INVALID_EMAIL_RECEIVED}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email__iexact=email).first()
            
            if not user:
                return Response({ERROR: USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            if user.role_type == "client":
                role = 'Cliente'
            elif user.role_type == "owner":
                role = 'Propietario'
            elif user.role_type == "worker":
                role = 'Trabajador'
            else:
                role = 'Desconocido'

            data = {
                "t": access,
                "refresh-token": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role_type": role,
                }
            }

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logging.exception("Error en Google login: %s", e)
            return Response({ERROR: INTERNAL_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
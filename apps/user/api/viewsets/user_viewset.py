import logging

from django.db.models import Q
from django_filters.rest_framework import CharFilter, DjangoFilterBackend, FilterSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.literals import (
    DETAILS,
    ERRORS,
    ERRORS_IN_REGISTRATION,
    ERRORS_IN_THE_INFORMATION,
    INTERNAL_ERROR,
    MESSAGE,
    PASSWORD_SUCCESSFULLY_UPDATED,
    USER_APP,
    USER_SUCCESSFULLY_DELETED,
    USER_SUCCESSFULLY_REGISTERED,
)
from apps.base.logger import configure_logging
from apps.base.permissions import IsOwnerOrStaffOrSuperUser, IsOwnerUser
from apps.user.api.serializers.user_serializers import (
    CreateUserSerializer,
    PartialUpdateUserSerializer,
    PasswordSerializer,
    UpdateUserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from apps.user.models.user import User

configure_logging()


class UserFilter(FilterSet):
    username = CharFilter(field_name="username", lookup_expr="icontains")
    email = CharFilter(field_name="email", lookup_expr="icontains")
    search = CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = ["username", "email", "is_active", "is_superuser", "is_staff", "search"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(Q(username__icontains=value) | Q(email__icontains=value))


class UserViewSet(viewsets.ModelViewSet):
    model = User
    queryset = User.objects.all().order_by("id")
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter

    def get_permissions(self):
        if self.action == "create":
            return [IsOwnerUser()]
        if self.action in ["update", "retrieve", "partial_update", "destroy", "list"]:
            return [IsAuthenticated(), IsOwnerOrStaffOrSuperUser()]
        if self.action in ["set_password", "profile"]:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        if self.action == "retrieve":
            return UserSerializer
        if self.action == "set_password":
            return PasswordSerializer
        if self.action == "update":
            return UpdateUserSerializer
        if self.action == "partial_update":
            return PartialUpdateUserSerializer
        if self.action == "profile":
            return UserProfileSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        try:
            logging.info(f"[user_viewset - list] {USER_APP}: Listing users.")
            queryset = self.filter_queryset(self.get_queryset())

            if not request.user.is_staff:
                queryset = queryset.filter(id=request.user.id)

            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                logging.info(f"[user_viewset - list] {USER_APP}: Users listed successfully.")
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            logging.info(f"[user_viewset - list] {USER_APP}: Users listed successfully.")
            return Response(serializer.data)
        except Exception as e:
            logging.error(f"[user_viewset - list] Error listando usuarios: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def set_password(self, request):
        try:
            logging.info(f"[user_viewset - set_password] {USER_APP}: Setting new password.")
            password_serializer = PasswordSerializer(data=request.data)
            user = request.user
            if password_serializer.is_valid():
                user.set_password(password_serializer.validated_data["password"])
                user.save()
                logging.info(f"[user_viewset - set_password] {USER_APP}: Password setted successfully.")
                return Response({MESSAGE: PASSWORD_SUCCESSFULLY_UPDATED})
            logging.error(f"[user_viewset - set_password] {USER_APP}: Failed when changing password.")
            return Response({MESSAGE: ERRORS_IN_THE_INFORMATION, ERRORS: password_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f"[user_viewset - set_password] Error cambiando password: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_queryset(self):
        queryset = super().get_queryset()

        username = self.request.query_params.get("username")
        email = self.request.query_params.get("email")

        if username:
            queryset = queryset.filter(username__icontains=username)

        if email:
            queryset = queryset.filter(email__icontains=email)

        return queryset

    def create(self, request):
        try:
            logging.info(f"[user_viewset - create] {USER_APP}: Creating a new User.")
            user_serializer = self.get_serializer_class()(data=request.data)
            if user_serializer.is_valid():
                user_serializer.save()
                logging.info(f"[user_viewset - create] {USER_APP}: Created new User.")
                return Response({MESSAGE: USER_SUCCESSFULLY_REGISTERED}, status=status.HTTP_201_CREATED)

            logging.error(f"[user_viewset - create] {USER_APP}: Failed when creating new User. {ERRORS}: {user_serializer.errors}")
            return Response({MESSAGE: ERRORS_IN_REGISTRATION, ERRORS: user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f"[user_viewset - create] Error creando usuario: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        try:
            user = self.get_object()
            logging.info(f"[user_viewset - destroy] {USER_APP}: Deleting User with id {pk}.")
            user.is_active = False
            user.save()
            logging.info(f"[user_viewset - destroy] {USER_APP}: Deleted User with id {pk}.")
            return Response({MESSAGE: USER_SUCCESSFULLY_DELETED})
        except Exception as e:
            logging.error(f"[user_viewset - destroy] Error eliminando usuario {pk}: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["get", "put"], url_path="profile")
    def profile(self, request):
        try:
            method = request.method.lower()
            user = request.user

            if method == "put":
                logging.info(f"[user_viewset - profile] {USER_APP}: Actualizando perfil de usuario.")
                serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)

                if serializer.is_valid():
                    serializer.save()
                    response_serializer = UserProfileSerializer(user)
                    logging.info(f"[user_viewset - profile] {USER_APP}: Perfil de usuario actualizado correctamente.")
                    return Response(response_serializer.data)

                logging.error(f"[user_viewset - profile] {USER_APP}: Fallo al actualizar el perfil de usuario. {ERRORS}: {serializer.errors}")
                return Response({MESSAGE: ERRORS_IN_THE_INFORMATION, ERRORS: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            if method == "get":
                serializer = UserProfileSerializer(user)
                logging.info(f"[user_viewset - profile] {USER_APP}: Perfil de usuario recuperado correctamente.")
                return Response(serializer.data)

            return Response({MESSAGE: ERRORS_IN_THE_INFORMATION}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logging.error(f"[user_viewset - profile] Error gestionando perfil: {str(e)}")
            return Response({DETAILS: {INTERNAL_ERROR: str(e)}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

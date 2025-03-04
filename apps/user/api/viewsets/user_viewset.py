import logging

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, CharFilter

from apps.base.literals import (
    MESSAGE,
    ERRORS,
    ERRORS_IN_THE_INFORMATION,
    PASSWORD_SUCCESSFULLY_UPDATED,
    USER_SUCCESSFULLY_REGISTERED,
    ERRORS_IN_REGISTRATION,
    USER_SUCCESSFULLY_DELETED,
    USER_APP
)
from apps.base.logger import configure_logging
configure_logging()

from apps.base.permissions import IsOwnerOrStaffOrSuperUser, IsOwnerUser
from apps.user.models.user import User
from apps.user.api.serializers.user_serializers import (
    CreateUserSerializer,
    PartialUpdateUserSerializer,
    PasswordSerializer,
    UpdateUserSerializer,
    UserSerializer
)


class UserFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')
    description = CharFilter(field_name='description', lookup_expr='icontains')
    
    class Meta:
        model = User
        fields = [
            'username',
            'email', 
            'is_active',
            'is_superuser',
            'is_staff'
        ]


class UserViewSet(viewsets.ModelViewSet):
    model = User
    queryset = User.objects.all().order_by('id')
    parser_classes = (MultiPartParser, FormParser,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsOwnerUser()]
        elif self.action in ['update', 'retrieve', 'partial_update', 'destroy', 'set_password', 'list']:
            return [IsAuthenticated(), IsOwnerOrStaffOrSuperUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'retrieve':
            return UserSerializer
        elif self.action == 'set_password':
            return PasswordSerializer
        elif self.action == 'update':
            return UpdateUserSerializer
        elif self.action == 'partial_update':
            return PartialUpdateUserSerializer
        return UserSerializer 

    def list(self, request, *args, **kwargs):
        logging.info(f"{USER_APP}: Listing users.")
        queryset = self.filter_queryset(self.get_queryset())
        
        if not request.user.is_staff:
            queryset = queryset.filter(id=request.user.id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logging.info(f"{USER_APP}: Users listed successfully.")
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        logging.info(f"{USER_APP}: Users listed successfully.")
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        logging.info(f"{USER_APP}: Setting new password.")
        password_serializer = PasswordSerializer(data=request.data)
        user = request.user
        if password_serializer.is_valid():
            user.set_password(password_serializer.validated_data['password'])
            user.save()
            logging.info(f"{USER_APP}: Password setted successfully.")
            return Response({MESSAGE: PASSWORD_SUCCESSFULLY_UPDATED})
        logging.error(f"{USER_APP}: Failed when changing password.")
        return Response({MESSAGE: ERRORS_IN_THE_INFORMATION, ERRORS: password_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        queryset = super().get_queryset()
        
        username = self.request.query_params.get('username', None)
        email = self.request.query_params.get('email', None)
        
        if username:
            queryset = queryset.filter(username__icontains=username)
            
        if email:
            queryset = queryset.filter(email__icontains=email)
            
        return queryset

    def create(self, request):
        logging.info(f"{USER_APP}: Creating a new User.")
        user_serializer = self.get_serializer_class()(data=request.data)
        if user_serializer.is_valid():
            user_serializer.save()
            logging.info(f"{USER_APP}: Created new User.")
            return Response({MESSAGE: USER_SUCCESSFULLY_REGISTERED}, status=status.HTTP_201_CREATED)
        
        logging.error(f"{USER_APP}: Failed when creating new User. \n{ERRORS}: {user_serializer.errors}")
        return Response({MESSAGE: ERRORS_IN_REGISTRATION, ERRORS: user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        user = self.get_object()
        logging.info(f"{USER_APP}: Deleting User with id {pk}.")
        user.is_active = False
        user.save()
        logging.info(f"{USER_APP}: Deleted User with id {pk}.")
        return Response({MESSAGE: USER_SUCCESSFULLY_DELETED})

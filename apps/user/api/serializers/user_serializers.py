from rest_framework import serializers
from apps.user.api.serializers.client_serializers import ClientSerializer
from apps.user.api.serializers.worker_serializers import WorkerSerializer
from apps.user.models.user import User
from apps.user.utils import sync_client_location_from_address


class CustomUserSerializer(serializers.ModelSerializer):
    role_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'email', 'role_type')

    def get_role_type(self, obj):
        if obj.role_type == "client":
            return 'Cliente'
        elif obj.role_type == "owner":
            return 'Propietario'
        elif obj.role_type == "worker":
            return 'Trabajador'
        return 'Desconocido'

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username','email', 'password')
    
    def create(self,validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
   
    
class UpdateUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ('username', 'email')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

        
class PartialUpdateUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if value:
                setattr(instance, attr, value)
        instance.save()
        return instance

        
class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, min_length=6, write_only=True)
    password2 = serializers.CharField(max_length=128, min_length=6, write_only=True)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {'password':'Debe ingresar ambas contraseñas iguales'}
            )
        return data


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

    def to_representation(self, instance):
        return {
            'id': instance['id'],
            'username': instance['username'],
            'email': instance['email']
        }


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)
    name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=255, trim_whitespace=True)
    surname = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=255, trim_whitespace=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20, trim_whitespace=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=255, trim_whitespace=True)
    dni = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=255, trim_whitespace=True)
    birth_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    cif = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=20, trim_whitespace=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100, trim_whitespace=True)
    postal_code = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=10, trim_whitespace=True)
    country = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=100, trim_whitespace=True)
    photo = serializers.ImageField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'email',
            'name',
            'surname',
            'phone',
            'address',
            'dni',
            'birth_date',
            'cif',
            'city',
            'postal_code',
            'country',
            'photo',
        ]

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            instance.email = validated_data['email']

        profile_fields = [
            'name',
            'surname',
            'phone',
            'address',
            'dni',
            'birth_date',
            'cif',
            'city',
            'postal_code',
            'country',
            'photo',
        ]
        profile_data = {k: v for k, v in validated_data.items() if k in profile_fields}

        if profile_data:
            profile = None
            if instance.role_type in ["owner", "worker"] and hasattr(instance, 'worker_profile'):
                profile = instance.worker_profile
            elif instance.role_type == "client" and hasattr(instance, 'client_profile'):
                profile = instance.client_profile
            elif hasattr(instance, 'worker_profile'):
                profile = instance.worker_profile
            elif hasattr(instance, 'client_profile'):
                profile = instance.client_profile

            if profile:
                address_changed = False
                for field, value in profile_data.items():
                    if not hasattr(profile, field):
                        continue
                    setattr(profile, field, value)
                    if field in ['address', 'city', 'postal_code', 'country']:
                        address_changed = True
                profile.save()

                if instance.role_type == "client" and address_changed:
                    sync_client_location_from_address(profile, clear_on_failure=True)

        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'is_staff', 'role_type', 'profile']

    def get_profile(self, obj):
        if obj.role_type in ["owner", "worker"] and hasattr(obj, 'worker_profile'):
            return WorkerSerializer(obj.worker_profile).data
        if obj.role_type == "client" and hasattr(obj, 'client_profile'):
            return ClientSerializer(obj.client_profile).data
        if hasattr(obj, 'worker_profile'):
            return WorkerSerializer(obj.worker_profile).data
        if hasattr(obj, 'client_profile'):
            return ClientSerializer(obj.client_profile).data
        return None

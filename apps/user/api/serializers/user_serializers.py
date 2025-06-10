from rest_framework import serializers
from apps.user.api.serializers.client_serializers import ClientSerializer
from apps.user.api.serializers.worker_serializers import WorkerSerializer
from apps.user.models.user import User


class CustomUserSerializer(serializers.ModelSerializer):
    role_type = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'role_type')

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
    name = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'phone']
        
    def update(self, instance, validated_data):
        if 'email' in validated_data:
            instance.email = validated_data['email']
            
        profile_fields = ['name', 'phone']
        profile_data = {k: v for k, v in validated_data.items() if k in profile_fields}
        
        if profile_data:
            if hasattr(instance, 'client_profile'):
                profile = instance.client_profile
            elif hasattr(instance, 'worker_profile'):
                profile = instance.worker_profile
            else:
                profile = None
                
            if profile:
                for field, value in profile_data.items():
                    setattr(profile, field, value)
                profile.save()
        
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'is_staff', 'role_type', 'profile']

    def get_profile(self, obj):
        if hasattr(obj, 'client_profile'):
            return ClientSerializer(obj.client_profile).data
        elif hasattr(obj, 'worker_profile'):
            return WorkerSerializer(obj.worker_profile).data
        return None
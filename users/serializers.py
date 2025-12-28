from rest_framework import serializers
from .models import CustomUser, Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'email', 'phone', 'role')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        # Add shop ID if owner?
        return token

class UserSerializer(serializers.ModelSerializer):
    shop_name = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()
    initial = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'phone', 'role', 'role_display', 
            'is_active', 'is_superuser', 'date_joined', 
            'shop_name', 'formatted_date', 'initial', 'status_display'
        )

    def get_shop_name(self, obj):
        # Owner -> Shop relationship
        if hasattr(obj, 'shops') and obj.shops.exists():
            return [shop.name for shop in obj.shops.all()]
        # Employee -> Shop relationship
        if hasattr(obj, 'shop') and obj.shop:
             return [obj.shop.name]
        return []

    def get_formatted_date(self, obj):
        return obj.date_joined.strftime("%b %d, %Y")

    def get_initial(self, obj):
        return obj.username[0].upper() if obj.username else "?"

    def get_status_display(self, obj):
        if obj.is_active: return "Active"
        return "Banned"

    def get_role_display(self, obj):
        if obj.is_superuser: return "Super Admin"
        if obj.role == 'OWNER': return "Owner"
        if obj.role == 'EMPLOYEE': return "Employee"
        return obj.role.title()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = (
            'id', 'username', 'email', 'phone', 'first_name', 'last_name', 
            'password', 'assigned_role', 'shop', 'branch', 'is_active', 'role'
        )
        extra_kwargs = {
            'role': {'read_only': True},
            'shop': {'read_only': True},  # Shop is set automatically based on logged-in owner
        }

    def create(self, validated_data):
        # Enforce role as EMPLOYEE
        validated_data['role'] = CustomUser.Role.EMPLOYEE
        
        # User create_user to handle password hashing
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user




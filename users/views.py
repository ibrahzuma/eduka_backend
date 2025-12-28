from rest_framework import generics, permissions
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import CustomUser

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class UserManagementAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        users = CustomUser.objects.all().order_by('-date_joined')
        
        # Search
        q = request.GET.get('q')
        if q:
            users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
            
        # Filter
        role = request.GET.get('role')
        if role:
            users = users.filter(role=role)
            
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class UserActionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        action = request.data.get('action')
        user_id = request.data.get('user_id')
        
        try:
            target_user = CustomUser.objects.get(id=user_id)
            if target_user.is_superuser:
                return Response({'error': 'Cannot modify Super Admin'}, status=status.HTTP_400_BAD_REQUEST)
            
            if action == 'ban':
                target_user.is_active = False
                target_user.save()
            elif action == 'activate':
                target_user.is_active = True
                target_user.save()
            elif action == 'delete':
                target_user.delete()
                return Response({'status': 'deleted'})
            else:
                return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({'status': 'success', 'is_active': target_user.is_active})
            
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

from .models import Role
from .serializers import RoleSerializer, EmployeeSerializer

class RoleListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
             return Role.objects.none()
             
        if user.is_superuser:
             return Role.objects.all()
        
        # Owner
        if hasattr(user, 'shops') and user.shops.exists():
            return Role.objects.filter(shop=user.shops.first())
            
        # Employee
        if hasattr(user, 'shop') and user.shop:
            return Role.objects.filter(shop=user.shop)
            
        return Role.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        shop = None
        
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
        elif hasattr(user, 'shop') and user.shop:
            shop = user.shop
            
        if not shop and not user.is_superuser:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"shop": "You must be associated with a shop to create a role."})
            
        serializer.save(shop=shop)

class RoleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated] # Changed from Admin to Authenticated (Owner)

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'shops') and user.shops.exists():
            return Role.objects.filter(shop=user.shops.first())
        return Role.objects.none()

class EmployeeListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CustomUser.objects.none()
            
        # If Owner, return their employees
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
            return CustomUser.objects.filter(shop=shop, role='EMPLOYEE')
            
        return CustomUser.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
            serializer.save(shop=shop, role='EMPLOYEE')
        else:
            # Fallback or error?
            serializer.save(role='EMPLOYEE')

class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure owners can only edit their own employees
        user = self.request.user
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
            return CustomUser.objects.filter(shop=shop, role='EMPLOYEE')
        return CustomUser.objects.none()

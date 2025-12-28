from django.urls import path
from .views import (
    RegisterView, CustomTokenObtainPairView, UserManagementAPIView, UserActionAPIView,
    RoleListCreateAPIView, RoleDetailAPIView, EmployeeListCreateAPIView, EmployeeDetailAPIView,
    MeAPIView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='auth_login'),
    path('me/', MeAPIView.as_view(), name='auth_me'),
    path('refresh/', TokenRefreshView.as_view(), name='auth_refresh'),
    path('manage/', UserManagementAPIView.as_view(), name='api_user_manage'),
    path('action/', UserActionAPIView.as_view(), name='api_user_action'),
    
    # Employee & Role Management
    path('roles/', RoleListCreateAPIView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', RoleDetailAPIView.as_view(), name='role-detail'),
    path('employees/', EmployeeListCreateAPIView.as_view(), name='employee-list-create'),
    path('employees/<int:pk>/', EmployeeDetailAPIView.as_view(), name='employee-detail'),
]

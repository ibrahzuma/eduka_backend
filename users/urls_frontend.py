from django.urls import path
from django.contrib.auth import views as auth_views
from . import views_frontend

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('register/', views_frontend.RegisterView.as_view(), name='register'),
    path('logout/', views_frontend.custom_logout_view, name='logout'),
    path('roles/', views_frontend.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views_frontend.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', views_frontend.RoleUpdateView.as_view(), name='role_edit'),
    path('employees/', views_frontend.EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', views_frontend.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/edit/', views_frontend.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/suspend/', views_frontend.EmployeeSuspendView.as_view(), name='employee_suspend'),
    path('employees/<int:pk>/delete/', views_frontend.EmployeeDeleteView.as_view(), name='employee_delete'),
    path('profile/', views_frontend.ProfileView.as_view(), name='profile'),
]





from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from shops.models import Shop, Branch, ShopSettings
from .models import Role
from .forms import (
    UserRegistrationForm, RoleForm, EmployeeForm, EmployeeEditForm, ProfileForm
)

User = get_user_model()

class RegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'auth/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'OWNER' # Enforce Owner role
            user.save()
            
            # Extract Business Data from Form
            business_name = form.cleaned_data.get('business_name')
            # business_type = form.cleaned_data.get('business_type') # Not in Shop model yet, ignore or add to description
            region = form.cleaned_data.get('region')
            district = form.cleaned_data.get('district')
            street = form.cleaned_data.get('street')
            
            # Create Shop automatically
            # Create Shop automatically
            shop = Shop.objects.create(owner=user, name=business_name)
            ShopSettings.objects.create(shop=shop)
            
            # Create Main Branch with Location Info
            address_str = f"{region}, {district}, {street}"
            Branch.objects.create(shop=shop, name='Main Branch', address=address_str, is_main=True)

            # Specify the backend to avoid MultipleBackends error
            # Using ModelBackend as default for registration-based login usually matches ModelBackend behavior
            # even if PhoneBackend is present. 
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return redirect('dashboard')
        return render(request, 'auth/register.html', {'form': form})

def custom_logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return render(request, 'auth/logout.html')


class RoleListView(LoginRequiredMixin, View):
    def get(self, request):
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            shop = request.user.shops.first()
        elif hasattr(request.user, 'shop') and request.user.shop:
            shop = request.user.shop
        else:
            shop = None
            
        roles = Role.objects.filter(shop=shop).order_by('-created_at') if shop else Role.objects.none()
        form = RoleForm()
        return render(request, 'users/role_list.html', {'roles': roles, 'form': form})

    def post(self, request):
        form = RoleForm(request.POST)
        shop = request.user.shops.first()
        if form.is_valid() and shop:
            role = form.save(commit=False)
            role.shop = shop
            role.save()
            messages.success(request, 'Role created successfully!', extra_tags='success')
            return redirect('role_list')
        
        roles = Role.objects.filter(shop=shop).order_by('-created_at') if shop else Role.objects.none()
        return render(request, 'users/role_list.html', {'roles': roles, 'form': form})

class RoleCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = RoleForm()
        # Define available permissions modules
        modules = [
            'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
            'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
        ]
        return render(request, 'users/role_create.html', {'form': form, 'modules': modules})

    def post(self, request):
        form = RoleForm(request.POST)
        
        # Determine Shop (Owner or Employee)
        shop = None
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            shop = request.user.shops.first()
        elif hasattr(request.user, 'shop') and request.user.shop:
            shop = request.user.shop
            
        if form.is_valid():
            role = form.save(commit=False)
            role.shop = shop # Assign the shop!
            
            # Process Permissions
            permissions = {}
            modules = [
                'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
                'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
            ]
            for module in modules:
                module_lower = module.lower()
                module_perms = []
                if request.POST.get(f'{module_lower}_view'): module_perms.append('view')
                if request.POST.get(f'{module_lower}_create'): module_perms.append('create')
                if request.POST.get(f'{module_lower}_edit'): module_perms.append('edit')
                if request.POST.get(f'{module_lower}_delete'): module_perms.append('delete')
                
                if module_perms:
                    permissions[module_lower] = module_perms
            
            role.permissions = permissions
            role.save()
            messages.success(request, 'Role created successfully with permissions!', extra_tags='success')
            return redirect('role_list')
        
        modules = [
            'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
            'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
        ]
        return render(request, 'users/role_create.html', {'form': form, 'modules': modules})

class RoleUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        form = RoleForm(instance=role)
        modules = [
            'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
            'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
        ]
        return render(request, 'users/role_edit.html', {'form': form, 'role': role, 'modules': modules})

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save(commit=False)
            
            # Process Permissions
            permissions = {}
            modules = [
                'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
                'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
            ]
            for module in modules:
                module_lower = module.lower()
                module_perms = []
                if request.POST.get(f'{module_lower}_view'): module_perms.append('view')
                if request.POST.get(f'{module_lower}_create'): module_perms.append('create')
                if request.POST.get(f'{module_lower}_edit'): module_perms.append('edit')
                if request.POST.get(f'{module_lower}_delete'): module_perms.append('delete')
                
                if module_perms:
                    permissions[module_lower] = module_perms
            
            role.permissions = permissions
            role.save()
            messages.success(request, 'Role updated successfully!', extra_tags='success')
            return redirect('role_list')
        
        modules = [
            'Dashboard', 'Sales', 'Purchases', 'Products', 'Services', 'Inventory', 
            'Returns', 'Clients', 'Finance', 'Expenses', 'Reports', 'Branches', 'Users', 'Settings'
        ]
        return render(request, 'users/role_edit.html', {'form': form, 'role': role, 'modules': modules})


class EmployeeListView(LoginRequiredMixin, View):
    def get(self, request):
        # Filter users who are marked as employees and belong to the current user's shop
        shop = request.user.shops.first() # Assuming one shop per owner for now
        if shop:
            employees = User.objects.filter(role='EMPLOYEE', shop=shop).order_by('-date_joined')
        else:
            employees = []
        return render(request, 'users/employee_list.html', {'employees': employees})

class EmployeeCreateView(LoginRequiredMixin, View):
    def get(self, request):
        shop = request.user.shops.first()
        form = EmployeeForm(shop=shop)
        return render(request, 'users/employee_create.html', {'form': form})

    def post(self, request):
        shop = request.user.shops.first()
        form = EmployeeForm(request.POST, shop=shop)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.shop = shop
            if form.cleaned_data.get('branch'):
                employee.branch = form.cleaned_data['branch']
            employee.save()
            messages.success(request, 'Employee added successfully!', extra_tags='success')
            return redirect('employee_list')
        return render(request, 'users/employee_create.html', {'form': form})

class EmployeeUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        employee = get_object_or_404(User, pk=pk, shop=request.user.shops.first())
        shop = request.user.shops.first()
        form = EmployeeEditForm(instance=employee, shop=shop)
        return render(request, 'users/employee_edit.html', {'form': form, 'employee': employee})

    def post(self, request, pk):
        employee = get_object_or_404(User, pk=pk, shop=request.user.shops.first())
        shop = request.user.shops.first()
        form = EmployeeEditForm(request.POST, instance=employee, shop=shop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully!', extra_tags='success')
            return redirect('employee_list')
        return render(request, 'users/employee_edit.html', {'form': form, 'employee': employee})

class EmployeeSuspendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        employee = get_object_or_404(User, pk=pk, shop=request.user.shops.first())
        if employee.is_active:
            employee.is_active = False
            messages.warning(request, f'Employee {employee.username} has been suspended.')
        else:
            employee.is_active = True
            messages.success(request, f'Employee {employee.username} has been reactivated.')
        employee.save()
        return redirect('employee_list')

class EmployeeDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        employee = get_object_or_404(User, pk=pk, shop=request.user.shops.first())
        employee.delete()
        messages.error(request, 'Employee has been permanently deleted.')
        return redirect('employee_list')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, 'users/profile.html', {'form': form})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!', extra_tags='success')
            return redirect('profile')
        return render(request, 'users/profile.html', {'form': form})

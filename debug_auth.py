import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model
from users.forms import EmployeeForm
from users.models import Role

User = get_user_model()

def test_authentication():
    print(">>> Setting up Test User...")
    username = "auth_test_user"
    password = "securePassword123"
    
    # ensure user doesn't exist
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()

    role, _ = Role.objects.get_or_create(name='Cashier')
    
    # 1. Create User via Form (Simulating real usage)
    data = {
        'first_name': 'Auth',
        'last_name': 'Tester',
        'username': username,
        'email': 'auth@test.com',
        'phone': '1231231234',
        'assigned_role': role.id,
        'password': password
    }
    
    form = EmployeeForm(data=data)
    if form.is_valid():
        user = form.save()
        print(f"User Created: {user.username} (ID: {user.id})")
        print(f"Is Active: {user.is_active}")
        print(f"Password Hashed: {user.password.startswith('pbkdf2_')}")
    else:
        print(f"Form Creation Failed: {form.errors}")
        return

    # 2. Test Authenticate (Simulating Login View)
    print("\n>>> Testing authenticate()...")
    # Case A: Correct Credentials
    user_auth = authenticate(username=username, password=password)
    if user_auth:
        print("SUCCESS: Authentication worked with valid credentials.")
    else:
        print("FAILED: Authentication returned None with valid credentials.")
        # Debugging why
        try:
            u_debug = User.objects.get(username=username)
            print(f"Debug - Check Password: {u_debug.check_password(password)}")
            print(f"Debug - Is Active: {u_debug.is_active}")
        except User.DoesNotExist:
            print("Debug - User not found in DB!")

    # Cleanup
    user.delete()

if __name__ == '__main__':
    test_authentication()

import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = "sabry"
password = "allahu(SW)1"

print(f"--- FIXING USER {username} ---")

try:
    user = User.objects.get(username=username)
    print(f"User '{username}' found.")
except User.DoesNotExist:
    print(f"User '{username}' not found. Creating...")
    user = User(username=username)

# Force Superuser Status
user.is_staff = True
user.is_superuser = True
user.set_password(password)

# Ensure no Role conflict (Super Admins rely on is_superuser, but let's set role too if model has it)
if hasattr(user, 'role'):
    user.role = 'SUPER_ADMIN'

user.save()

print(f"SUCCESS: User '{username}' is now a Superuser with the specified password.")
print(f"is_superuser: {user.is_superuser}")
print(f"is_staff: {user.is_staff}")
print("-------------------------------")

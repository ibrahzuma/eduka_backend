import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from users.models import Role, CustomUser

def check_roles():
    print(">>> Checking Roles and Permissions...")
    roles = Role.objects.all()
    for role in roles:
        print(f"Role: {role.name} (ID: {role.id})")
        print(f"Permissions: {role.permissions}")
        print("-" * 30)

    print("\n>>> Checking Verify Employee Permissions...")
    # Find an employee
    employee = CustomUser.objects.filter(role='EMPLOYEE').last()
    if employee:
        print(f"Employee: {employee.username}")
        print(f"Assigned Role: {employee.assigned_role}")
        if employee.assigned_role:
            print(f"Role Perms: {employee.assigned_role.permissions}")
        else:
            print("WARNING: No assigned role!")
    else:
        print("No employees found.")

if __name__ == '__main__':
    check_roles()

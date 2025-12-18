import os
import django
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from dashboard.views import DashboardTemplateView
from shops.models import Shop, Branch
from users.models import Role

User = get_user_model()

def test_dashboard_access():
    print(">>> Setting up Environment...")
    # Create Owner
    owner, _ = User.objects.get_or_create(username='owner_debug', email='owner@debug.com', role='OWNER')
    shop, _ = Shop.objects.get_or_create(owner=owner, name='Debug Shop')
    branch, _ = Branch.objects.get_or_create(shop=shop, name='Debug Branch')
    
    # Create Role
    role, created = Role.objects.get_or_create(name='DebugRole')
    role.permissions = {'sales': ['view']}
    role.save()
    
    # Create Employee WITH Branch
    username = 'emp_branch_debug'
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
        
    user = User.objects.create_user(username=username, password='password123', email='emp@debug.com', role='EMPLOYEE')
    user.shop = shop
    user.branch = branch # ASSIGN BRANCH causing potential crash
    user.assigned_role = role
    user.save()
    
    print(f"User Created: {user.username} | Shop: {user.shop} | Branch: {user.branch}")

    # Simulate Request to Dashboard
    factory = RequestFactory()
    request = factory.get('/dashboard/')
    request.user = user
    
    print("\n>>> Render Dashboard View...")
    try:
        # Load permission tags library manually if needed or rely on template loader
        from django.template import Context, Template
        
        view = DashboardTemplateView.as_view()
        response = view(request)
        print(f"Response Code: {response.status_code}")
        
        if response.status_code == 200:
             print("SUCCESS: Dashboard rendered.")
             response.render()
             content = response.content.decode('utf-8')
             
             # Check for generic Sidebar elements or permission-based elements
             if 'Dashboard' in content: 
                 print("Sidebar 'Dashboard' link found.")
                 
             if 'Sales' in content:
                 print("Sidebar 'Sales' link found.")
                 if 'data-bs-target="#collapseSales"' in content:
                     print("  -> Sales is ACTIVE (Has dropdown toggle).")
                 else:
                     print("  -> Sales is LOCKED (No dropdown toggle).")
             
             if 'Finance' in content:
                 print("Sidebar 'Finance' link found.")
                 if 'data-bs-target="#collapseFinance"' in content:
                     print("  -> Finance is ACTIVE (Has dropdown toggle). [SUCCESS: Branch Override Working]")
                 else:
                     print("  -> Finance is LOCKED. [FAIL: Branch Override Not Working]")
             else:
                 print("WARNING: Sidebar 'Finance' link NOT found.")
                 
             # Dump FULL content
             with open('dashboard_render.html', 'w', encoding='utf-8') as f:
                 f.write(content)
             print("Dumped full dashboard content to dashboard_render.html")

    except Exception as e:
        print(f"FATAL ERROR: Dashboard Crashed: {e}")
        import traceback
        traceback.print_exc()

    # Cleanup
    user.delete()
    branch.delete()
    shop.delete()
    owner.delete()

if __name__ == '__main__':
    test_dashboard_access()

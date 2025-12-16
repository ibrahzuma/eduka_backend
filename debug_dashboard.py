import os
import sys
import django
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from dashboard.views import DashboardTemplateView

User = get_user_model()

print("--- DIAGNOSTIC START ---")

try:
    # 1. Get a test user (Non-Superuser)
    user = User.objects.filter(is_superuser=False).first()
    if not user:
        print("WARNING: No non-superuser found. Testing with ANY user.")
        user = User.objects.first()
        
    print(f"Testing with user: {user.username} (ID: {user.id})")
    print(f"Is Superuser: {user.is_superuser}")
    
    # 2. Simulate Request
    factory = RequestFactory()
    request = factory.get('/dashboard/')
    request.user = user
    
    # 3. Instantiate View
    view = DashboardTemplateView()
    view.request = request
    
    print("Executing get_context_data()...")
    context = view.get_context_data()
    
    print("Context generated successfully.")
    print("--- TESTING TEMPLATE RENDERING ---")
    from django.template.loader import render_to_string
    rendered = render_to_string('dashboard/index.html', context, request=request)
    print("Template rendered successfully (Length: {} chars)".format(len(rendered)))
    
    print("--- SUCCESS ---")
    
except Exception as e:
    print("\n--- CRASH DETECTED ---")
    import traceback
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")

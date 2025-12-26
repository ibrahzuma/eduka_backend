import os
import django
from django.conf import settings
from django.template import Context, Template, RequestContext
from django.test import RequestFactory
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.template.loader import get_template
from dashboard.views import DashboardTemplateView

User = get_user_model()

def debug_render():
    print("--- STARTING DEBUG RENDER ---")
    try:
        # 1. Create Employee User
        user, created = User.objects.get_or_create(username="debug_emp_noshop")
        if created:
            user.set_password("password")
            user.role = 'EMPLOYEE'
            user.shop = None # Explicitly None
            user.save()
            
        print(f"User: {user} (Role: {user.role})")

        # 2. Create Request
        factory = RequestFactory()
        request = factory.get('/dashboard/')
        request.user = user
        # Mock resolver match
        from django.urls import resolve
        request.resolver_match = resolve('/dashboard/')

        # 3. Get Context from View
        view = DashboardTemplateView()
        view.request = request
        view.object = None
        
        print("Getting Context Data...")
        context = view.get_context_data()
        print("Context Keys:", context.keys())

        # 4. Render Template
        print("Rendering Template...")
        t = get_template('dashboard/index.html')
        # We need to render it with the request context to trigger context processors
        rendered_html = t.render(context, request=request)
        
        print("SUCCESS: Template rendered successfully.")
        print("Length:", len(rendered_html))

    except Exception:
        print("\n!!! EXCEPTION DURING RENDER !!!")
        traceback.print_exc()

if __name__ == "__main__":
    debug_render()

import os
import django

# Setup Django environment BEFORE any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

# Now safe to import DRF and models
from django.conf import settings
from rest_framework.test import APIRequestFactory, force_authenticate
from users.models import CustomUser
from users.views import MeAPIView

def verify_me_endpoint():
    print("--- Verifying User Profile 'Me' API ---")
    
    # Get or create test user
    user, _ = CustomUser.objects.get_or_create(
        username='test_me_user', 
        defaults={
            'email': 'me@example.com',
            'role': 'OWNER'
        }
    )
    
    factory = APIRequestFactory()
    
    # Test Me API
    print("Testing GET /api/auth/me/ ...")
    view = MeAPIView.as_view()
    request = factory.get('/api/auth/me/')
    force_authenticate(request, user=user)
    response = view(request)
    
    assert response.status_code == 200
    assert response.data['username'] == 'test_me_user'
    assert response.data['role'] == 'OWNER'
    assert 'role_display' in response.data
    
    print(f"SUCCESS: Profile fetched for user '{response.data['username']}' with role '{response.data['role']}'.")
    print("\n--- User Profile API Test Passed ---")

if __name__ == "__main__":
    try:
        verify_me_endpoint()
    except Exception as e:
        print(f"ERROR during verification: {e}")
        import traceback
        traceback.print_exc()

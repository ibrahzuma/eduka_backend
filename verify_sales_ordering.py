import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from sales.models import Sale
from rest_framework.test import APIRequestFactory, force_authenticate
from sales.views import SaleViewSet
from users.models import CustomUser

def verify_ordering():
    factory = APIRequestFactory()
    view = SaleViewSet.as_view({'get': 'list'})
    
    # Get a user who has sales
    user = CustomUser.objects.filter(is_superuser=True).first()
    if not user:
        print("No superuser found for testing.")
        return

    request = factory.get('/api/sales/sales/')
    force_authenticate(request, user=user)
    response = view(request)
    
    if response.status_code == 200:
        results = response.data.get('results', [])
        if len(results) >= 2:
            created_at_1 = results[0]['created_at']
            created_at_2 = results[1]['created_at']
            print(f"First sale date: {created_at_1}")
            print(f"Second sale date: {created_at_2}")
            
            if created_at_1 >= created_at_2:
                print("SUCCESS: Sales are correctly ordered (most recent first).")
            else:
                print("FAILURE: Sales are NOT correctly ordered.")
        elif len(results) == 1:
            print("Only one sale found, cannot verify ordering between items, but API is functional.")
        else:
            print("No sales found to verify ordering.")
    else:
        print(f"API Request failed with status code {response.status_code}")

if __name__ == "__main__":
    verify_ordering()

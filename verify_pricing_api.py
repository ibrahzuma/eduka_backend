import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate

from dashboard.views import PricingAPIView
from users.models import CustomUser

def verify():
    print("--- Verifying Pricing API ---")
    factory = RequestFactory()
    request = factory.get('/api/pricing/')
    
    # Test as standard user (Non-Superuser) to check is_active filter
    user = CustomUser.objects.create_user('pricetest', 'price@test.com', 'pass')
    request.user = user
    
    view = PricingAPIView.as_view()
    response = view(request)
    
    print(f"Status Code: {response.status_code}")
    print(f"Data: {response.data}")
    
    if len(response.data) == 0:
        print("WARNING: No plans found via API!")
    else:
        for plan in response.data:
            print(f"Plan: {plan.get('name')} (ID: {plan.get('id')})")
            print(f" - Daily: {plan.get('price_daily')}")
            print(f" - Monthly: {plan.get('price_monthly')}")
            print(f" - Active: {plan.get('is_active')}")

    user.delete()
    print("--- Verification Complete ---")

if __name__ == '__main__':
    verify()

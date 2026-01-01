import os
import django
from unittest.mock import MagicMock, patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduka_backend.settings")
django.setup()

from subscriptions.clickpesa_service import ClickPesaService
from subscriptions.views import CheckPaymentStatusView
from subscriptions.models import SubscriptionPayment

def test_url_config():
    print("Testing URL Configuration...")
    service = ClickPesaService()
    # Mock settings.CLICKPESA_API_URL if needed, but assuming it's set in env/settings
    # For this test, we just check if it's NOT the hardcoded one if settings differ
    print(f"Service API URL: {service.api_url}")
    
    # Check if initiate_ussd_push uses it
    with patch('subscriptions.clickpesa_service.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'success': True}
        service.initiate_ussd_push('255712345678', '5000', 'TEST_REF')
        
        args, kwargs = mock_post.call_args
        called_url = args[0]
        print(f"Initiate URL called: {called_url}")
        
        if service.api_url in called_url:
            print("PASS: Service is using configured API URL.")
        else:
            print("FAIL: Service might still be using hardcoded URL.")

def test_status_parsing():
    print("\nTesting Status Parsing Logic...")
    
    # We can't easily mock the View without a request, so we'll test the logic concepts
    # Or strict mock
    
    statuses_to_test = ['SUCCESS', 'Success', 'successful', 'COMPLETED', 'Paid']
    
    SUCCESS_STATUSES = ['SUCCESS', 'COMPLETED', 'PAID', 'SUCCESSFUL']
    
    for status in statuses_to_test:
        normalized = status.upper()
        if normalized in SUCCESS_STATUSES:
            print(f"Status '{status}' -> '{normalized}': WOULD SUCCEED")
        else:
            print(f"Status '{status}' -> '{normalized}': WOULD FAIL")

if __name__ == "__main__":
    test_url_config()
    test_status_parsing()

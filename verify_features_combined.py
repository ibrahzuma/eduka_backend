
import os
import django
from django.conf import settings
from decimal import Decimal
import json
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from shops.models import Shop, Branch
from inventory.models import Product, Category, Stock
from finance.views_ocr import analyze_receipt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

User = get_user_model()
client = Client()

def verify_all():
    print("=== Verifying Features ===")
    
    # Setup User and Shop
    user, _ = User.objects.get_or_create(username='verify_admin', defaults={'email': 'verify@test.com'})
    shop, _ = Shop.objects.get_or_create(name='Verify Shop', owner=user)
    shop.slug = 'verify-shop'
    shop.public_visibility = True
    shop.save()
    
    branch, _ = Branch.objects.get_or_create(shop=shop, name='Main')
    product, _ = Product.objects.get_or_create(
        shop=shop, 
        name='Happy Milk', 
        defaults={'selling_price': 1000, 'is_public': True}
    )
    product.selling_price = 1000
    product.is_public = True
    product.save()

    # 1. Verify Public Storefront
    print("\n--- 1. Public Storefront ---")
    url = f"/store/{shop.slug}/"
    resp = client.get(url)
    if resp.status_code == 200:
        if 'Happy Milk' in str(resp.content):
            print("SUCCESS: Public store accessible and product listed.")
        else:
            print("FAILURE: Public store accessible but product MISSING.")
    else:
        print(f"FAILURE: Status Code {resp.status_code}")

    # 2. Verify OCR
    print("\n--- 2. Expense OCR ---")
    # We use a mock file
    with open('test_receipt.jpg', 'wb') as f:
        f.write(b'fake image content')
    
    with open('test_receipt.jpg', 'rb') as f:
        data = {'receipt': f}
        # Note: We need to use valid URL. `eduka_backend/urls.py` mounts finance at /api/finance/
        # and finance/urls.py has analyze-receipt/
        url_ocr = "/api/finance/analyze-receipt/" 
        resp_ocr = client.post(url_ocr, data, format='multipart')
    
    if os.path.exists('test_receipt.jpg'):
        os.remove('test_receipt.jpg')
        
    if resp_ocr.status_code == 200:
        json_data = resp_ocr.json()
        if 'vendor' in json_data and 'amount' in json_data:
            print(f"SUCCESS: OCR processed. Vendor: {json_data['vendor']}, Amount: {json_data['amount']}")
        else:
            print("FAILURE: JSON missing keys.")
    else:
        print(f"FAILURE: OCR Status Code {resp_ocr.status_code} - {resp_ocr.content}")

if __name__ == "__main__":
    verify_all()

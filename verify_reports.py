import os
import django
import requests
import json
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from sales.models import Sale, SaleItem
from purchase.models import PurchaseOrder, Supplier
from finance.models import Expense
from inventory.models import Product, StockMovement, Category, Stock
from shops.models import Shop, Branch

User = get_user_model()

def verify_reports():
    # Setup Data
    user = User.objects.filter(username='admin').first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        
    shop, _ = Shop.objects.get_or_create(owner=user, name="Test Shop")
    branch, _ = Branch.objects.get_or_create(shop=shop, name="Main Branch")
    category, _ = Category.objects.get_or_create(shop=shop, name="Test Category")
    product, _ = Product.objects.get_or_create(shop=shop, category=category, name="Test Product", defaults={'selling_price': 100, 'cost_price': 50})
    stock, _ = Stock.objects.get_or_create(product=product, branch=branch, defaults={'quantity': 100})
    
    # Create Disposal Movement
    StockMovement.objects.create(
        stock=stock, product=product, branch=branch, 
        quantity_change=-1, movement_type='DISPOSAL',
        reason='Damaged', user=user
    )

    client = APIClient()
    client.force_authenticate(user=user)

    endpoints = [
        '/api/reports/sales/',
        '/api/reports/purchases/',
        '/api/reports/pricing/',
        '/api/reports/disposal/',
        '/api/reports/expenses/',
        '/api/reports/income-statement/',
        '/api/reports/cashflow/',
    ]

    print("Verifying Endpoints...")
    all_passed = True
    for endpoint in endpoints:
        response = client.get(endpoint)
        if response.status_code == 200:
            print(f"[PASS] {endpoint}")
            # print(json.dumps(response.data, indent=2))
        else:
            print(f"[FAIL] {endpoint} - Status: {response.status_code}")
            print(response.data)
            all_passed = False

    if all_passed:
        print("\nAll endpoints verified successfully!")
    else:
        print("\nSome verification failed.")

if __name__ == "__main__":
    verify_reports()


import os
import django
from datetime import timedelta
from decimal import Decimal
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from django.utils import timezone
from users.models import CustomUser
from shops.models import Shop, Branch
from inventory.models import Product, Stock, Category
from sales.models import Sale, SaleItem
from inventory.forecasting import SalesForecaster

def verify_forecasting():
    print("Setting up test data...")
    
    # 1. Setup User and Shop
    user = CustomUser.objects.first()
    if not user:
        print("No user found.")
        return

    shop, _ = Shop.objects.get_or_create(name="Test Shop", owner=user)
    branch, _ = Branch.objects.get_or_create(shop=shop, name="Main Branch")
    category, _ = Category.objects.get_or_create(shop=shop, name="Test Category")
    
    # 2. Setup Product
    product, _ = Product.objects.get_or_create(
        shop=shop,
        name="Test Milk",
        defaults={'selling_price': 1000, 'category': category}
    )
    
    # 3. Setup Stock (Current Quantity = 10)
    stock, _ = Stock.objects.get_or_create(product=product, branch=branch)
    stock.quantity = 20
    stock.save()
    
    # 4. Create Sales History (Sold 10 items over last 5 days = 2 per day)
    # We clear existing sales for this product to be sure
    SaleItem.objects.filter(product=product).delete()
    
    now = timezone.now()
    sale = Sale.objects.create(shop=shop, branch=branch, cashier=user, total_amount=10000)
    
    # Sale 1: 5 days ago, Qty 4
    s1 = Sale.objects.create(shop=shop, branch=branch, cashier=user, created_at=now - timedelta(days=5))
    s1.created_at = now - timedelta(days=5) # Hack to override auto_now_add
    s1.save()
    SaleItem.objects.create(sale=s1, product=product, quantity=4, price=1000)
    
    # Sale 2: 2 days ago, Qty 6
    s2 = Sale.objects.create(shop=shop, branch=branch, cashier=user, created_at=now - timedelta(days=2))
    s2.created_at = now - timedelta(days=2)
    s2.save()
    SaleItem.objects.create(sale=s2, product=product, quantity=6, price=1000)
    
    print("Test Data Created: Stock=20, Sold 10 in last 5 days (Actual Avg = 2/day over 5 days, but we forecast over 30 days usually)")

    # 5. Verify Logic
    forecaster = SalesForecaster()
    
    # Predict daily usage over last 30 days
    # Total sold = 10. Days = 30. Avg = 10/30 = 0.33
    daily_usage_30 = forecaster.predict_daily_usage(product, shop, days=30)
    print(f"\n[30 Days] Daily Usage: {daily_usage_30} (Expected ~0.33)")
    
    # Predict daily usage over last 7 days
    # Total sold = 10. Days = 7. Avg = 10/7 = 1.42
    daily_usage_7 = forecaster.predict_daily_usage(product, shop, days=7)
    print(f"[7 Days]  Daily Usage: {daily_usage_7} (Expected ~1.42)")
    
    # Predict Run-out Date (using default 30 days logic inside predict_runout_date?)
    # The method uses predict_daily_usage(days=30) by default in my implementation?
    # Let's check implementation behavior.
    runout_date, days_left, status = forecaster.predict_runout_date(stock)
    
    print(f"\nRun-out Prediction (Based on 30-day avg ~0.33):")
    print(f"Current Stock: {stock.quantity}")
    print(f"Days Left: {days_left}")
    print(f"Est Date: {runout_date}")
    print(f"Status: {status}")
    
    if days_left and days_left > 0:
        print("SUCCESS: Run-out date calculated.")
    else:
        print("FAILURE: Run-out date not calculated correctly.")

if __name__ == '__main__':
    verify_forecasting()

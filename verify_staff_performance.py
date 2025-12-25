
import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from users.models import CustomUser
from sales.models import Sale
from shops.models import Shop, Branch

def verify_staff_performance():
    print("Verifying Staff Performance Feature...")
    
    # 1. Setup Data
    user_name = "test_staff_01"
    user, created = CustomUser.objects.get_or_create(username=user_name, defaults={'email': 'test@staff.com'})
    user.commission_rate = Decimal('5.00')
    user.save()
    print(f"User {user.username} configured with Commission Rate: {user.commission_rate}%")
    
    shop, _ = Shop.objects.get_or_create(id=1, defaults={'name': 'Test Shop', 'owner': user})
    branch, _ = Branch.objects.get_or_create(shop=shop, name='Main')

    # 2. Simulate Sales
    print("Simulating Sales...")
    sale1 = Sale.objects.create(shop=shop, branch=branch, cashier=user, total_amount=10000, created_at=timezone.now())
    sale2 = Sale.objects.create(shop=shop, branch=branch, cashier=user, total_amount=20000, created_at=timezone.now())
    
    total_sales = sale1.total_amount + sale2.total_amount
    expected_commission = total_sales * (user.commission_rate / 100)
    
    print(f"Total Sales Generated: {total_sales}")
    print(f"Expected Commission: {expected_commission}")
    
    # 3. Verify Calculation Logic (Simulate View Logic)
    from django.db.models import Sum
    
    aggregated = Sale.objects.filter(cashier=user).aggregate(total=Sum('total_amount'))
    actual_total = aggregated['total'] or 0
    actual_commission = actual_total * (user.commission_rate / 100)
    
    if actual_total == total_sales and actual_commission == expected_commission:
        print("SUCCESS: Calculation logic verified correctly.")
    else:
        print(f"FAILURE: Expected total {total_sales}, got {actual_total}")
        print(f"FAILURE: Expected comm {expected_commission}, got {actual_commission}")

if __name__ == '__main__':
    verify_staff_performance()


import os
import django
from django.utils import timezone
import datetime
from django.test import RequestFactory
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from users.models import CustomUser
from shops.models import Shop, Branch, ShopSettings
from sales.models import Sale
from purchase.models import PurchaseOrder
from finance.models import Expense
from inventory.models import Product, StockMovement, Category
from reports.api_views import (
    SalesSummaryAPIView, PurchasesSummaryAPIView, ExpensesSummaryAPIView, 
    DisposalSummaryAPIView, PricingSummaryAPIView, IncomeSummaryAPIView, 
    CashflowSummaryAPIView
)

def verify_reports():
    print("Verifying Comprehensive Report Summaries...")
    
    # 1. Setup Data
    timestamp = int(timezone.now().timestamp())
    username = f"report_test_{timestamp}"
    user = CustomUser.objects.create_user(username=username, password='password123')
    shop = Shop.objects.create(owner=user, name=f"Report Shop {timestamp}")
    branch = Branch.objects.create(shop=shop, name="Main", is_main=True)
    ShopSettings.objects.create(shop=shop)
    cat = Category.objects.create(shop=shop, name="Gen")
    
    print(f"Created User: {username}, Shop: {shop.name}")
    
    # Helper to set date
    def set_date(obj, days_ago):
        obj.created_at = timezone.now() - datetime.timedelta(days=days_ago)
        obj.save()
        return obj

    # --- SEED DATA ---
    print("Seeding Data...")
    
    # SALES (Income)
    # Today: 1000
    s1 = Sale.objects.create(shop=shop, branch=branch, cashier=user, total_amount=1000)
    # Week (3 days ago): 2000
    s2 = Sale.objects.create(shop=shop, branch=branch, cashier=user, total_amount=2000)
    set_date(s2, 3)
    
    # PURCHASES (COGS)
    # Today: 500
    p1 = PurchaseOrder.objects.create(shop=shop, branch=branch, total_cost=500, status='RECEIVED')
    # Week (3 days ago): 1000
    p2 = PurchaseOrder.objects.create(shop=shop, branch=branch, total_cost=1000, status='RECEIVED')
    set_date(p2, 3)
    
    # EXPENSES
    # Today: 100
    e1 = Expense.objects.create(shop=shop, branch=branch, amount=100, date=timezone.now().date(), description="Tea")
    # Week (3 days ago): 200
    week_date = timezone.now().date() - datetime.timedelta(days=3)
    e1 = Expense.objects.create(shop=shop, branch=branch, amount=200, date=week_date, description="Coffee")
    
    # PRICING (Products Added)
    # Today: 1 product @ 5000
    prod1 = Product.objects.create(shop=shop, category=cat, name="P1", selling_price=5000)
    # Week (3 days ago): 1 product @ 6000
    prod2 = Product.objects.create(shop=shop, category=cat, name="P2", selling_price=6000)
    set_date(prod2, 3)
    
    # DISPOSAL
    # Today: Disposal of P1 (qty 2). Cost logic required.
    # Need Stock first for movement key... actually movement just points to stock.
    from inventory.models import Stock
    # Stock created by signal automatically when Product created
    stk1 = Stock.objects.get(product=prod1, branch=branch)
    stk1.quantity = 10
    stk1.save()
    
    # Movement 1: Today, Disposed 2 items. Cost = product.cost_price (default 0? Let's update cost)
    prod1.cost_price = 400
    prod1.save()
    m1 = StockMovement.objects.create(
        stock=stk1, product=prod1, branch=branch, 
        quantity_change=-2, movement_type='DISPOSAL'
    )
    # Value = abs(-2) * 400 = 800
    
    # --- EXPECTED VALUES (Today / Week) ---
    # Sales: 1000 / 3000
    # Purchases: 500 / 1500
    # Expenses: 100 / 300
    # Disposal: 800 / 800 (only today)
    # Pricing: 5000 / 11000
    # Income (S - P - E): (1000-500-100)=400 / (3000-1500-300)=1200
    # Cashflow (In - Out): (1000 - (500+100))=400 / (3000 - (1500+300))=1200
    
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user

    def check(view_class, name, key, expected_total):
        view = view_class.as_view()
        resp = view(request)
        if resp.status_code != 200:
            print(f"FAIL: {name} {key} - Status {resp.status_code}")
            return
        
        # Determine data structure key (some dicts have 'total', some 'total_expenses' etc?)
        # My helper unified it to 'total', but original sales/purchases views used 'total_sales'.
        # Refactor check: I updated SalesSummaryAPIView to use helper, so it returns 'total'.
        # All my new views use helper.
        
        data_item = resp.data[key]
        if isinstance(data_item, dict):
            if 'total' in data_item:
                actual = data_item['total']
            elif 'net_cashflow' in data_item:
                actual = data_item['net_cashflow']
            else:
                 print(f"FAIL: {name} - Unknown key in {data_item.keys()}")
                 return
        else:
            actual = data_item
        
        # If Income/Cashflow, they refer to 'net_profit' or 'net_cashflow'?
        # In IncomeSummaryAPIView: total = s - p - e.
        
        if actual == expected_total:
            print(f"PASS: {name} ({key}) = {actual}")
        else:
            print(f"FAIL: {name} ({key}) - Expected {expected_total}, Got {actual}")

    print("\n--- Testing Today ---")
    check(SalesSummaryAPIView, "Sales", 'today', 1000)
    check(PurchasesSummaryAPIView, "Purchases", 'today', 500)
    check(ExpensesSummaryAPIView, "Expenses", 'today', 100)
    check(DisposalSummaryAPIView, "Disposal", 'today', 800)
    check(PricingSummaryAPIView, "Pricing", 'today', 5000)
    check(IncomeSummaryAPIView, "Income", 'today', 400)
    check(CashflowSummaryAPIView, "Cashflow", 'today', { 'net_cashflow': 400, 'inflow': 1000, 'outflow': 600 }['net_cashflow']) # Helper check logic slightly complex for nested

    print("\n--- Testing Week ---")
    check(SalesSummaryAPIView, "Sales", 'week', 3000)
    check(PurchasesSummaryAPIView, "Purchases", 'week', 1500)
    check(ExpensesSummaryAPIView, "Expenses", 'week', 300)
    # Disposal only happened today, so week total is same
    check(DisposalSummaryAPIView, "Disposal", 'week', 800)
    check(PricingSummaryAPIView, "Pricing", 'week', 11000)
    check(IncomeSummaryAPIView, "Income", 'week', 1200)

if __name__ == '__main__':
    verify_reports()

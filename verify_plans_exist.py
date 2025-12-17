
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from subscriptions.models import SubscriptionPlan

print(f"Total Plans: {SubscriptionPlan.objects.count()}")

plans = SubscriptionPlan.objects.all()
for p in plans:
    print(f"ID: {p.id} Name: {p.name} Active: {p.is_active}")
    print(f"Prices: D={p.price_daily} W={p.price_weekly} M={p.price_monthly}")
    
active_plans = SubscriptionPlan.objects.filter(is_active=True)
print(f"Active Plans Count: {active_plans.count()}")

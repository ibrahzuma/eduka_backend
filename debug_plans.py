import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduka_backend.settings")
django.setup()

from subscriptions.models import SubscriptionPlan

def check_plans():
    print("Checking Subscription Plans...")
    plans = SubscriptionPlan.objects.all()
    for p in plans:
        print(f"ID: {p.id} | Name: {p.name} | Weekly: {p.price_weekly} | Monthly: {p.price_monthly}")

if __name__ == "__main__":
    check_plans()

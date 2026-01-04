import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduka_backend.settings')
django.setup()

from subscriptions.models import SubscriptionPlan

def update_plans():
    plans = SubscriptionPlan.objects.all()
    print(f"Updating {plans.count()} plans...")
    for plan in plans:
        plan.max_shops = 1
        plan.max_users = 5
        plan.max_products = 10000
        
        # Ensure priority support is in features
        features = plan.features or {}
        features['priority_support'] = True
        plan.features = features
        
        plan.save()
        print(f"Updated {plan.name}")

if __name__ == '__main__':
    update_plans()

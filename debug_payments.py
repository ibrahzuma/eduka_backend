import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eduka_backend.settings")
django.setup()

from subscriptions.models import SubscriptionPayment

def check_payments():
    print("Checking recent Subscription Payments...")
    payments = SubscriptionPayment.objects.all().order_by('-created_at')[:10]
    
    if not payments:
        print("No payments found.")
        return

    for p in payments:
        print(f"ID: {p.id} | Amount: {p.amount} | Status: {p.status} | Ref: {p.transaction_id} | Date: {p.created_at}")

if __name__ == "__main__":
    check_payments()

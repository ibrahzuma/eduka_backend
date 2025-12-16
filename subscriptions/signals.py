from django.db.models.signals import post_save
from django.dispatch import receiver
from shops.models import Shop
from .models import ShopSubscription, SubscriptionPlan
from django.utils import timezone
from datetime import timedelta

@receiver(post_save, sender=Shop)
def create_shop_subscription(sender, instance, created, **kwargs):
    if created:
        # Get or Create a 'Trial' Plan
        trial_plan, _ = SubscriptionPlan.objects.get_or_create(
            slug='trial',
            defaults={
                'name': 'Free Trial',
                'description': '7-Day Free Trial',
                'price_daily': 0.00,
                'price_weekly': 0.00,
                'price_monthly': 0.00,
                'price_quarterly': 0.00,
                'price_biannually': 0.00,
                'price_yearly': 0.00,
                'max_shops': 1,
                'max_users': 1,
                'max_products': 50
            }
        )
        
        # Create Subscription
        ShopSubscription.objects.create(
            shop=instance,
            plan=trial_plan,
            status='TRIAL',
            billing_cycle='WEEKLY',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7)
        )

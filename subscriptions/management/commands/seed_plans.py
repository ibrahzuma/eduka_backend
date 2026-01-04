from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Seeds default subscription plans'

    def handle(self, *args, **options):
        self.stdout.write("Checking Subscription Plans...")
        
        if SubscriptionPlan.objects.count() == 0:
            self.stdout.write("No plans found. Creating defaults...")
            
            SubscriptionPlan.objects.create(
                name='Starter',
                slug='starter',
                description='Perfect for small shops just getting started.',
                price_daily=500,
                price_weekly=2500,
                price_monthly=10000,
                price_quarterly=28000,
                price_biannually=55000,
                price_yearly=100000,
                max_shops=1,
                max_users=5,
                max_products=10000,
                features={
                    'priority_support': True,
                    'backup': 'Daily',
                },
                is_active=True
            )
            
            SubscriptionPlan.objects.create(
                name='Pro',
                slug='pro',
                description='For growing businesses that need more power.',
                price_daily=1000,
                price_weekly=5000,
                price_monthly=20000,
                price_quarterly=55000,
                price_biannually=100000,
                price_yearly=180000,
                max_shops=1,
                max_users=5,
                max_products=10000,
                features={
                    'priority_support': True,
                    'backup': 'Realtime',
                },
                is_active=True
            )
            
            self.stdout.write(self.style.SUCCESS('Successfully created Starter and Pro plans.'))
        else:
            self.stdout.write("Plans already exist. Checking active status...")
            updated = SubscriptionPlan.objects.filter(is_active=False).update(is_active=True)
            if updated > 0:
                 self.stdout.write(self.style.SUCCESS(f'Activated {updated} existing plans.'))
            else:
                 self.stdout.write(self.style.SUCCESS('Plans are already set up.'))

from django.db import models
from django.utils import timezone
from shops.models import Shop


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100) # e.g. Free, Starter, Pro
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    
    # New Pricing Fields (0.00 = Disabled)
    price_daily = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_weekly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_quarterly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_biannually = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # 6 Months
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Feature Gating & Limits
    max_shops = models.IntegerField(default=1)
    max_users = models.IntegerField(default=1)
    max_products = models.IntegerField(default=100)
    features = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ShopSubscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('TRIAL', 'Trial'),
    ]
    
    CYCLE_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', '3 Months'),
        ('BIANNUALLY', '6 Months'),
        ('YEARLY', 'Yearly'),
    ]

    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRIAL')
    
    # New field to track the selected cycle
    billing_cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='MONTHLY')
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid(self):
        return self.status in ['ACTIVE', 'TRIAL'] and self.end_date > timezone.now()

    def __str__(self):
        return f"{self.shop.name} - {self.plan.name} ({self.status})"

class SubscriptionPayment(models.Model):
    subscription = models.ForeignKey(ShopSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=50) # e.g. Stripe, PayPal, M-Pesa
    status = models.CharField(max_length=20, default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.amount}"

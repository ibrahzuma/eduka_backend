from django.db import models
from django.conf import settings

class Shop(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shops')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='shops/logos/', null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    public_visibility = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ShopSettings(models.Model):
    class Plan(models.TextChoices):
        TRIAL = 'TRIAL', 'Trial'
        DUKA = 'DUKA', 'Duka'
        ENTERPRISE = 'ENTERPRISE', 'Enterprise'

    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='settings')
    currency = models.CharField(max_length=10, default='TZS')
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Billing Info
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.TRIAL)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)
    billing_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # e.g. 60,000

    def __str__(self):
        return f"Settings for {self.shop.name}"

class Branch(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shop.name} - {self.name}"

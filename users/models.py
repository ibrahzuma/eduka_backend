from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        OWNER = 'OWNER', 'Owner'
        EMPLOYEE = 'EMPLOYEE', 'Employee'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    assigned_role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    # Employee Fields
    shop = models.ForeignKey('shops.Shop', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    branch = models.ForeignKey('shops.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Commission percentage (e.g. 5.00 for 5%)")
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.SUPER_ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Manager, Cashier")
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, blank=True) # Data structure: {'sales': ['manage'], 'inventory': ['view', 'edit']}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

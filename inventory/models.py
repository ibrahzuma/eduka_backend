from django.db import models
from django.conf import settings
from shops.models import Shop, Branch

class Category(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('shop', 'name')

    def __str__(self):
        return f"{self.name} ({self.shop.name})"

class Product(models.Model):
    class Type(models.TextChoices):
        GOODS = 'GOODS', 'Goods'
        SERVICE = 'SERVICE', 'Service'

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=255)
    product_type = models.CharField(max_length=10, choices=Type.choices, default=Type.GOODS)
    sku = models.CharField(max_length=100, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    si_unit = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Kilo, Dozen, Pcs")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    # Service might not have cost price or stock, handled in logic.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)

    class Meta:
        unique_together = ('product', 'branch')

    def __str__(self):
        return f"{self.product.name} - {self.branch.name}: {self.quantity}"

class StockMovement(models.Model):
    class Type(models.TextChoices):
        ADD = 'ADD', 'Add'
        REDUCE = 'REDUCE', 'Reduce'
        SET = 'SET', 'Set'
        SALE = 'SALE', 'Sale'
        PURCHASE = 'PURCHASE', 'Purchase'
        DISPOSAL = 'DISPOSAL', 'Disposal'
        DAMAGED = 'DAMAGED', 'Damaged'
        EXPIRED = 'EXPIRED', 'Expired'

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    quantity_change = models.IntegerField(help_text="Positive for addition, Negative for reduction")
    movement_type = models.CharField(max_length=20, choices=Type.choices)
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.product.name} ({self.movement_type}): {self.quantity_change}"

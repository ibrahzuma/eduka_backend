from django.db import models
from django.conf import settings
from shops.models import Shop, Branch
from customers.models import Customer
from inventory.models import Product

class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        CARD = 'CARD', 'Card'
        MOBILE = 'MOBILE', 'Mobile'
        CREDIT = 'CREDIT', 'Credit'

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sales')
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_history')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount}"

    @property
    def invoice_number(self):
        return f"INV-{self.created_at.strftime('%Y')}-{self.id:05d}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True) # If product deleted, keep record?
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2) # Snapshot of price

    @property
    def get_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name if self.product else 'Unknown'} ({self.quantity})"

class SaleReturn(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    reason = models.TextField(blank=True, null=True)
    total_refund = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Return #{self.id} for Sale #{self.sale.id}"

class SaleReturnItem(models.Model):
    return_ref = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    refund_price = models.DecimalField(max_digits=10, decimal_places=2) # Price at time of return (usually same as sale price)

    def __str__(self):
        return f"Return Item: {self.product.name} ({self.quantity})"

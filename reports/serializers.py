from rest_framework import serializers
from sales.models import Sale, SaleItem
from purchase.models import PurchaseOrder, PurchaseItem
from finance.models import Expense
from inventory.models import Product, StockMovement

class ReportSaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = ['product_name', 'quantity', 'price', 'get_total']

class ReportSaleSerializer(serializers.ModelSerializer):
    items = ReportSaleItemSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source='cashier.get_full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Sale
        fields = ['id', 'invoice_number', 'total_amount', 'payment_method', 'payment_method_display', 'created_at', 'cashier_name', 'items']

class ReportPurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseItem
        fields = ['product_name', 'quantity', 'unit_cost']

class ReportPurchaseSerializer(serializers.ModelSerializer):
    items = ReportPurchaseItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'supplier_name', 'total_cost', 'status', 'status_display', 'created_at', 'items']

class ReportExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'category', 'description', 'amount', 'date']

class ReportProductPricingSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'category_name', 'cost_price', 'selling_price', 'sku', 'barcode']

class ReportStockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = StockMovement
        fields = ['id', 'product_name', 'branch_name', 'quantity_change', 'movement_type', 'type_display', 'reason', 'created_at', 'user_name']

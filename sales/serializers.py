from rest_framework import serializers
from .models import Sale, SaleItem

class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = SaleItem
        fields = '__all__'
        read_only_fields = ('sale',)

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    cashier_name = serializers.CharField(source='cashier.username', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ('cashier', 'created_at', 'shop')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        total = 0
        from inventory.models import Stock, StockMovement
        
        for item_data in items_data:
            quantity = item_data['quantity']
            price = item_data['price']
            total += price * quantity
            product_id = item_data['product'].id
            
            # Create Sale Item
            SaleItem.objects.create(sale=sale, **item_data)
            
            # Deduct Stock
            # Find stock for this product at this branch
            # validated_data has 'branch' which is a Branch instance
            branch = validated_data['branch']
            
            stock_qs = Stock.objects.filter(product_id=product_id, branch=branch)
            if stock_qs.exists():
                stock = stock_qs.first()
                stock.quantity -= quantity
                stock.save()
            else:
                # Optionally create negative stock? Or ignore?
                # For now, let's create it if missing with negative qty (allow overdraft)
                Stock.objects.create(product_id=product_id, branch=branch, quantity=-quantity)
                
        sale.total_amount = total
        sale.save()
        return sale

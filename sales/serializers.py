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
        read_only_fields = ('cashier', 'created_at')

    def create(self, validated_data):
        from .utils_pricing import calculate_price
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        total = 0
        for item_data in items_data:
            product = item_data.get('product') # Assuming this is a Product instance due to ModelSerializer
            
            # Recalculate price server-side
            if product:
                final_price, _, _ = calculate_price(product, sale.shop)
                item_data['price'] = final_price
            
            total += item_data['price'] * item_data['quantity']
            SaleItem.objects.create(sale=sale, **item_data)
        sale.total_amount = total
        sale.save()
        return sale

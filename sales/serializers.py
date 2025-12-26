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
        items_data = validated_data.pop('items')
        sale = Sale.objects.create(**validated_data)
        total = 0
        for item_data in items_data:
            # product = item_data.get('product')
            
            total += item_data['price'] * item_data['quantity']
            SaleItem.objects.create(sale=sale, **item_data)
        sale.total_amount = total
        sale.save()
        return sale

from rest_framework import viewsets, permissions
from .models import Category, Product, Stock
from .serializers import CategorySerializer, ProductSerializer, StockSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            return Category.objects.all()
        # Fix for Employees
        if hasattr(user, 'shops') and user.shops.exists():
            return Category.objects.filter(shop=user.shops.first())
        elif hasattr(user, 'shop') and user.shop:
            return Category.objects.filter(shop=user.shop)
        return Category.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        shop = None
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
        elif hasattr(user, 'shop') and user.shop:
            shop = user.shop
        
        if shop:
            serializer.save(shop=shop)
        else:
            raise ValidationError({"shop": "No shop found for user."})

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            return Product.objects.all()
        # Fix for Employees
        if hasattr(user, 'shops') and user.shops.exists():
            return Product.objects.filter(shop=user.shops.first())
        elif hasattr(user, 'shop') and user.shop:
            return Product.objects.filter(shop=user.shop)
        return Product.objects.none()
        
    def perform_create(self, serializer):
        # Auto-assign shop for Products too
        user = self.request.user
        shop = None
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
        elif hasattr(user, 'shop') and user.shop:
            shop = user.shop
            
        if shop:
            serializer.save(shop=shop)
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"shop": "No shop found."})

class StockViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StockSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            return Stock.objects.all()
        
        # Fix for Employees
        if hasattr(user, 'shops') and user.shops.exists():
            return Stock.objects.filter(branch__shop=user.shops.first())
        elif hasattr(user, 'shop') and user.shop:
            return Stock.objects.filter(branch__shop=user.shop)
        return Stock.objects.none()

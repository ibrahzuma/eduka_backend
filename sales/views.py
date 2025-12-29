from rest_framework import viewsets, permissions
from .models import Sale
from .serializers import SaleSerializer

class SaleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaleSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            return Sale.objects.all()
        
        # Check User's Shop (Owner or Employee)
        if hasattr(user, 'shops') and user.shops.exists():
            return Sale.objects.filter(shop=user.shops.first())
        elif hasattr(user, 'shop') and user.shop: # Direct FK if model differs, or property 
             # Based on user model analysis, employee has user.shop_id or user.employee_profile.shop
             # Let's check how other views do it. Dashboard used user.shop_id.
             if user.role == 'EMPLOYEE' and user.shop_id:
                 return Sale.objects.filter(shop_id=user.shop_id)

        # Fallback for Owner logic if 'shops' rel is standard
        # Fallback for Owner logic if 'shops' rel is standard
        return Sale.objects.filter(shop__owner=user)

    def perform_create(self, serializer):
        user = self.request.user
        shop = None
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
        elif hasattr(user, 'shop') and user.shop:
            shop = user.shop
        
        if shop:
            serializer.save(shop=shop, cashier=user)
        else:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"shop": "No shop found."})

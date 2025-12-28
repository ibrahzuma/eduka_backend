from rest_framework import viewsets, permissions
from .models import Customer
from .serializers import CustomerSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomerSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Customer.objects.none()
            
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            return Customer.objects.all()
            
        # Determine Shop
        if hasattr(user, 'shops') and user.shops.exists():
            return Customer.objects.filter(shop=user.shops.first())
        elif hasattr(user, 'shop') and user.shop:
            return Customer.objects.filter(shop=user.shop)
            
        return Customer.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        shop = None
        
        if hasattr(user, 'shops') and user.shops.exists():
            shop = user.shops.first()
        elif hasattr(user, 'shop') and user.shop:
            shop = user.shop
            
        if not shop:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"shop": "No shop associated with this user."})
            
        serializer.save(shop=shop)

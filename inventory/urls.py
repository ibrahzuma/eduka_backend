from django.urls import path, include
from rest_framework import routers
from .views import CategoryViewSet, ProductViewSet, StockViewSet

router = routers.SimpleRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stocks', StockViewSet, basename='stock')

urlpatterns = [
    # path('', include(router.urls)),
]

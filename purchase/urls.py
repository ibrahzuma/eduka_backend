from rest_framework import routers
from .views import SupplierViewSet, PurchaseOrderViewSet

router = routers.SimpleRouter()
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'orders', PurchaseOrderViewSet, basename='purchase-order')

urlpatterns = router.urls

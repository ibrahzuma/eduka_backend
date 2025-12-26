from rest_framework import routers
from .views import SaleViewSet

router = routers.SimpleRouter()
router.register(r'sales', SaleViewSet, basename='sale')

urlpatterns = router.urls

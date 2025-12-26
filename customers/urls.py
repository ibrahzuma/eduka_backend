from rest_framework import routers
from .views import CustomerViewSet

router = routers.SimpleRouter()
router.register(r'customers', CustomerViewSet, basename='customer')

urlpatterns = router.urls

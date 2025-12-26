from rest_framework import routers
from .views import ShopViewSet, BranchViewSet, ShopSettingsViewSet

router = routers.SimpleRouter()
router.register(r'shops', ShopViewSet, basename='shop')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'settings', ShopSettingsViewSet, basename='settings')

urlpatterns = router.urls

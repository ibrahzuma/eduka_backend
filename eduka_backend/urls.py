from django.contrib import admin
from django.urls import path, include
from shops import views_frontend as shops_views
from shops import views_public as public_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/shops/', include('shops.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/purchase/', include('purchase.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/finance/', include('finance.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('accounts/', include('users.urls_frontend')),
    path('shops/', include('shops.urls_frontend')),
    path('inventory/', include('inventory.urls_frontend')),
    path('sales/', include('sales.urls_frontend')),
    path('purchase/', include('purchase.urls_frontend')),
    path('finance/', include('finance.urls_frontend')),
    path('subscriptions/', include('subscriptions.urls')),
    path('accounts/', include('allauth.urls')), # Allauth routes
    path('customers/', include('customers.urls_frontend')),
    path('reports/', include('reports.urls_frontend')),
    path('api/reports/', include('reports.urls')),
    path('', include('dashboard.urls_frontend')), # Main Dashboard
    path('settings/', shops_views.ShopSettingsView.as_view(), name='settings'),
    path('store/<slug:slug>/', public_views.PublicShopView.as_view(), name='public_store'),
]

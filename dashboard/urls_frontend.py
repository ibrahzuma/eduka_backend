from django.urls import path
from . import views
from .views import DashboardTemplateView, SettingsView # Keep this if used elsewhere or remove if fully switched to views.


urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('dashboard/', DashboardTemplateView.as_view(), name='dashboard'),
    path('dashboard/superuser/', views.SuperUserDashboardView.as_view(), name='superuser_dashboard'),
    path('dashboard/superuser/crm/', views.SuperUserCRMView.as_view(), name='superuser_crm'),
    path('dashboard/superuser/shops/', views.SuperUserShopListView.as_view(), name='superuser_shop_list'),
    path('dashboard/superuser/shops/create/', views.SuperUserShopCreateView.as_view(), name='superuser_shop_create'),
    path('dashboard/superuser/shops/<int:pk>/edit/', views.SuperUserShopUpdateView.as_view(), name='superuser_shop_update'),
    path('dashboard/superuser/shops/<int:pk>/delete/', views.SuperUserShopDeleteView.as_view(), name='superuser_shop_delete'),
    
    path('dashboard/superuser/plans/', views.SubscriptionPlanListView.as_view(), name='superuser_plan_list'),
    path('dashboard/superuser/plans/create/', views.SubscriptionPlanCreateView.as_view(), name='superuser_plan_create'),
    path('dashboard/superuser/plans/<int:pk>/edit/', views.SubscriptionPlanUpdateView.as_view(), name='superuser_plan_update'),
    path('dashboard/superuser/plans/<int:pk>/edit/', views.SubscriptionPlanUpdateView.as_view(), name='superuser_plan_update'),
    path('dashboard/superuser/plans/<int:pk>/delete/', views.SubscriptionPlanDeleteView.as_view(), name='superuser_plan_delete'),
    path('dashboard/superuser/plans/<int:pk>/delete/', views.SubscriptionPlanDeleteView.as_view(), name='superuser_plan_delete'),
    path('dashboard/superuser/settings/', views.SuperUserGlobalSettingsView.as_view(), name='superuser_settings'),
    path('dashboard/superuser/settings/', views.SuperUserGlobalSettingsView.as_view(), name='superuser_settings'),
    path('dashboard/superuser/broadcast/', views.SuperUserBroadcastView.as_view(), name='superuser_broadcast'),
    path('dashboard/superuser/users/', views.SuperUserUserListView.as_view(), name='superuser_user_list'),
    path('dashboard/superuser/users/<int:pk>/delete/', views.SuperUserUserDeleteView.as_view(), name='superuser_user_delete'),
    
    path('dashboard/pricing/', views.ShopPricingView.as_view(), name='shop_pricing'),
    
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('api/notifications/list/', views.NotificationListAPIView.as_view(), name='api_notifications_list'),
    path('api/notifications/read/', views.NotificationMarkReadAPIView.as_view(), name='api_notifications_read'),
    path('api/pricing/', views.PricingAPIView.as_view(), name='api_pricing'),
]

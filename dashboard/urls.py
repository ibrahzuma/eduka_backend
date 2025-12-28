from django.urls import path
from .views import (
    DashboardSummaryView, SuperUserDashboardView, PricingAPIView,
    NotificationListAPIView, NotificationMarkReadAPIView
)

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('pricing/', PricingAPIView.as_view(), name='api_pricing'),
    path('superuser/', SuperUserDashboardView.as_view(), name='superuser_dashboard'),
    path('notifications/', NotificationListAPIView.as_view(), name='api_notifications'),
    path('notifications/mark-read/', NotificationMarkReadAPIView.as_view(), name='api_notifications_mark_read'),
]

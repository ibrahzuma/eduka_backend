from django.urls import path
from .views import DashboardSummaryView, SuperUserDashboardView, PricingAPIView

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('pricing/', PricingAPIView.as_view(), name='api_pricing'),
    path('superuser/', SuperUserDashboardView.as_view(), name='superuser_dashboard'),
]

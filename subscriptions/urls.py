from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('initiate-payment/', views.InitiatePaymentView.as_view(), name='initiate_payment'),
    path('check-status/<int:payment_id>/', views.CheckPaymentStatusView.as_view(), name='check_payment_status'),
    path('api/plans/', api_views.SubscriptionPlanListView.as_view(), name='api_sub_plans'),
    path('api/status/', api_views.SubscriptionStatusAPIView.as_view(), name='api_sub_status'),
    # Support for /api/subscriptions/ prefix (Flutter App)
    path('plans/', api_views.SubscriptionPlanListView.as_view(), name='api_sub_plans_direct'),
    path('status/', api_views.SubscriptionStatusAPIView.as_view(), name='api_sub_status_direct'),
]

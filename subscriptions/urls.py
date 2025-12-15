from django.urls import path
from .views import InitiatePaymentView, CheckPaymentStatusView

urlpatterns = [
    path('pay/initiate/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('pay/status/<int:payment_id>/', CheckPaymentStatusView.as_view(), name='check_payment_status'),
]

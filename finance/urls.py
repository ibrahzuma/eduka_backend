from rest_framework import routers
from .views import ExpenseViewSet

from django.urls import path, include
from . import views_frontend, views_ocr

router = routers.SimpleRouter()
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('analyze-receipt/', views_ocr.analyze_receipt, name='analyze_receipt'),
    path('', include(router.urls)),
]

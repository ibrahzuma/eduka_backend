from django.urls import path
from .api_views import (
    SalesReportAPIView, PurchasesReportAPIView, PricingReportAPIView, DisposalReportAPIView,
    ExpensesReportAPIView, IncomeStatementAPIView, CashflowAPIView
)

urlpatterns = [
    path('sales/', SalesReportAPIView.as_view(), name='api_report_sales'),
    path('purchases/', PurchasesReportAPIView.as_view(), name='api_report_purchases'),
    path('pricing/', PricingReportAPIView.as_view(), name='api_report_pricing'),
    path('disposal/', DisposalReportAPIView.as_view(), name='api_report_disposal'),
    path('expenses/', ExpensesReportAPIView.as_view(), name='api_report_expenses'),
    path('income-statement/', IncomeStatementAPIView.as_view(), name='api_report_income_statement'),
    path('cashflow/', CashflowAPIView.as_view(), name='api_report_cashflow'),
]

from django.urls import path
from .views_frontend import (
    SalesReportView, PurchasesReportView, PricingReportView, DisposalReportView,
    ExpensesReportView, IncomeStatementView, CashflowView, ForecastingView
)

urlpatterns = [
    path('sales/', SalesReportView.as_view(), name='report_sales'),
    path('purchases/', PurchasesReportView.as_view(), name='report_purchases'),
    path('pricing/', PricingReportView.as_view(), name='report_pricing'),
    path('disposal/', DisposalReportView.as_view(), name='report_disposal'),
    path('expenses/', ExpensesReportView.as_view(), name='report_expenses'),
    path('income-statement/', IncomeStatementView.as_view(), name='report_income_statement'),
    path('cashflow/', CashflowView.as_view(), name='report_cashflow'),
    path('forecasting/', ForecastingView.as_view(), name='report_forecasting'),
]

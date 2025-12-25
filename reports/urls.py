from django.urls import path
from .api_views import (
    SalesReportAPIView, PurchasesReportAPIView, PricingReportAPIView, DisposalReportAPIView,
    ExpensesReportAPIView, IncomeStatementAPIView, CashflowAPIView, SalesSummaryAPIView,
    PurchasesSummaryAPIView, ExpensesSummaryAPIView, DisposalSummaryAPIView, PricingSummaryAPIView,
    IncomeSummaryAPIView, CashflowSummaryAPIView
)

urlpatterns = [
    path('sales/', SalesReportAPIView.as_view(), name='api_report_sales'),
    path('sales/summary/', SalesSummaryAPIView.as_view(), name='api_report_sales_summary'),
    path('purchases/', PurchasesReportAPIView.as_view(), name='api_report_purchases'),
    path('purchases/summary/', PurchasesSummaryAPIView.as_view(), name='api_report_purchases_summary'),
    path('pricing/', PricingReportAPIView.as_view(), name='api_report_pricing'),
    path('pricing/summary/', PricingSummaryAPIView.as_view(), name='api_report_pricing_summary'),
    path('disposal/', DisposalReportAPIView.as_view(), name='api_report_disposal'),
    path('disposal/summary/', DisposalSummaryAPIView.as_view(), name='api_report_disposal_summary'),
    path('expenses/', ExpensesReportAPIView.as_view(), name='api_report_expenses'),
    path('expenses/summary/', ExpensesSummaryAPIView.as_view(), name='api_report_expenses_summary'),
    path('income-statement/', IncomeStatementAPIView.as_view(), name='api_report_income_statement'),
    path('income-statement/summary/', IncomeSummaryAPIView.as_view(), name='api_report_income_summary'),
    path('cashflow/', CashflowAPIView.as_view(), name='api_report_cashflow'),
    path('cashflow/summary/', CashflowSummaryAPIView.as_view(), name='api_report_cashflow_summary'),
]

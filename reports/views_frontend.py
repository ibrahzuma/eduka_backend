from django.views.generic import ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth, TruncDate
from sales.models import Sale
from purchase.models import PurchaseOrder
from finance.models import Expense
from inventory.models import Product, Stock
import datetime
from django.utils.dateparse import parse_date
from inventory.forecasting import SalesForecaster

class ForecastingView(LoginRequiredMixin, TemplateView):
    template_name = "reports/forecasting.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if getattr(self.request.user, 'shop', None):
            shop = self.request.user.shop
        elif hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
            shop = self.request.user.shops.first()
        else:
            shop = None

        if not shop:
            return context

        forecaster = SalesForecaster()
        predictions = []
        
        # Get all stocks for this shop with positive quantity
        stocks = Stock.objects.filter(branch__shop=shop, quantity__gt=0).select_related('product', 'branch')
        
        for stock in stocks:
            runout_date, days_left, status = forecaster.predict_runout_date(stock)
            daily_usage = forecaster.predict_daily_usage(stock.product, shop)
            
            if daily_usage > 0: # Only show items with usage
                predictions.append({
                    'product': stock.product.name,
                    'branch': stock.branch.name,
                    'current_stock': stock.quantity,
                    'daily_usage': round(daily_usage, 2),
                    'days_left': days_left,
                    'runout_date': runout_date,
                    'status': status
                })
        
        # Sort by urgency (days left)
        predictions.sort(key=lambda x: x['days_left'])
        
        context['predictions'] = predictions
        return context

class BaseShopView(LoginRequiredMixin):
    def get_shop(self):
        # 1. Direct check for Employee's assigned shop
        if getattr(self.request.user, 'shop', None):
            return self.request.user.shop
            
        # 2. Check for Owner's shops
        if hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
            return self.request.user.shops.first()
            
        # 3. Legacy fallback
        if hasattr(self.request.user, 'employee_profile'):
             return self.request.user.employee_profile.shop
             
        return None

class ReportDateFilterMixin:
    def get_date_range(self):
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None
        
        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date, end_date = self.get_date_range()
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Add quick filter flags for UI active state
        filter_type = self.request.GET.get('filter')
        if filter_type:
            context['current_filter'] = filter_type
            
        return context

class SalesReportView(ReportDateFilterMixin, BaseShopView, ListView):
    model = Sale
    template_name = 'reports/sales_report.html'
    context_object_name = 'sales'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            qs = Sale.objects.filter(shop=shop).select_related('customer').order_by('-created_at')
            start_date, end_date = self.get_date_range()
            if start_date:
                qs = qs.filter(created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(created_at__date__lte=end_date)
            return qs
        return Sale.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            qs = self.get_queryset()
            context['total_sales'] = qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            context['total_count'] = qs.count()
        return context

class PurchasesReportView(ReportDateFilterMixin, BaseShopView, ListView):
    model = PurchaseOrder
    template_name = 'reports/purchases_report.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            qs = PurchaseOrder.objects.filter(shop=shop).select_related('supplier').order_by('-created_at')
            start_date, end_date = self.get_date_range()
            if start_date:
                qs = qs.filter(created_at__date__gte=start_date)
            if end_date:
                qs = qs.filter(created_at__date__lte=end_date)
            return qs
        return PurchaseOrder.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            qs = self.get_queryset()
            context['total_purchases'] = qs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        return context

class ExpensesReportView(ReportDateFilterMixin, BaseShopView, ListView):
    model = Expense
    template_name = 'reports/expenses_report.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            qs = Expense.objects.filter(shop=shop).order_by('-date')
            start_date, end_date = self.get_date_range()
            if start_date:
                qs = qs.filter(date__gte=start_date)
            if end_date:
                qs = qs.filter(date__lte=end_date)
            return qs
        return Expense.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            qs = self.get_queryset()
            context['total_expenses'] = qs.aggregate(Sum('amount'))['amount__sum'] or 0
        return context

class IncomeStatementView(ReportDateFilterMixin, BaseShopView, TemplateView):
    template_name = 'reports/income_statement.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            start_date, end_date = self.get_date_range()
            
            sales_qs = Sale.objects.filter(shop=shop)
            purchases_qs = PurchaseOrder.objects.filter(shop=shop)
            expenses_qs = Expense.objects.filter(shop=shop)

            if start_date:
                sales_qs = sales_qs.filter(created_at__date__gte=start_date)
                purchases_qs = purchases_qs.filter(created_at__date__gte=start_date)
                expenses_qs = expenses_qs.filter(date__gte=start_date)
            
            if end_date:
                sales_qs = sales_qs.filter(created_at__date__lte=end_date)
                purchases_qs = purchases_qs.filter(created_at__date__lte=end_date)
                expenses_qs = expenses_qs.filter(date__lte=end_date)

            total_sales = sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            total_purchases = purchases_qs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
            
            context['total_income'] = total_sales
            context['total_cogs'] = total_purchases
            context['gross_profit'] = total_sales - total_purchases
            context['total_expenses'] = total_expenses
            context['net_profit'] = context['gross_profit'] - total_expenses
        return context

class PlaceholderView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/placeholder.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.request.path.strip('/').replace('/', ' ').replace('-', ' ').title()
        return context

class PricingReportView(ReportDateFilterMixin, BaseShopView, ListView):
    model = Product
    template_name = 'reports/pricing_report.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            # Pricing is typically current state, but filtering by creation date or update allowed
            return Product.objects.filter(shop=shop).select_related('category')
        return Product.objects.none()

class DisposalReportView(ReportDateFilterMixin, BaseShopView, ListView):
    """Showing items with 0 stock or explicitly marked as disposed"""
    model = Stock
    template_name = 'reports/disposal_report.html'
    context_object_name = 'disposals'
    
    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            # Note: Stock model doesn't have created_at usually, referencing updated_at or movement if complex
            # For now, simplistic filtering if available, else ignored for stock snapshot
            return Stock.objects.filter(branch__shop=shop, quantity=0).select_related('product', 'branch')
        return Stock.objects.none()

class CashflowView(ReportDateFilterMixin, BaseShopView, TemplateView):
    template_name = 'reports/cashflow.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            start_date, end_date = self.get_date_range()
            
            sales_qs = Sale.objects.filter(shop=shop)
            purchases_qs = PurchaseOrder.objects.filter(shop=shop)
            expenses_qs = Expense.objects.filter(shop=shop)
            
            if start_date:
                sales_qs = sales_qs.filter(created_at__date__gte=start_date)
                purchases_qs = purchases_qs.filter(created_at__date__gte=start_date)
                expenses_qs = expenses_qs.filter(date__gte=start_date)
            
            if end_date:
                sales_qs = sales_qs.filter(created_at__date__lte=end_date)
                purchases_qs = purchases_qs.filter(created_at__date__lte=end_date)
                expenses_qs = expenses_qs.filter(date__lte=end_date)

            total_sales = sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            total_purchases = purchases_qs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
            
            context['inflow'] = total_sales
            context['outflow'] = total_purchases + total_expenses
            context['net_cashflow'] = context['inflow'] - context['outflow']
        return context

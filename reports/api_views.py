from rest_framework import views, permissions, response
from django.db.models import Sum
from sales.models import Sale
from purchase.models import PurchaseOrder
from finance.models import Expense
from inventory.models import Product, StockMovement
from .serializers import (
    ReportSaleSerializer, ReportPurchaseSerializer, ReportExpenseSerializer, 
    ReportProductPricingSerializer, ReportStockMovementSerializer
)
import datetime
from django.utils.dateparse import parse_date

class ReportBaseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_shop(self):
        user = self.request.user
        if getattr(user, 'shop', None):
            return user.shop
        if hasattr(user, 'shops') and user.shops.exists():
            return user.shops.first()
        if hasattr(user, 'employee_profile'):
            return user.employee_profile.shop
        return None

    def get_date_range(self):
        start_date_str = self.request.query_params.get('start_date')
        end_date_str = self.request.query_params.get('end_date')
        
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None
        
        return start_date, end_date

class SalesReportAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        queryset = Sale.objects.filter(shop=shop).order_by('-created_at')
        start_date, end_date = self.get_date_range()
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        total_sales = queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_count = queryset.count()
        
        serializer = ReportSaleSerializer(queryset, many=True)
        return response.Response({
            'total_sales': total_sales,
            'total_count': total_count,
            'sales': serializer.data
        })

class PurchasesReportAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        queryset = PurchaseOrder.objects.filter(shop=shop).order_by('-created_at')
        start_date, end_date = self.get_date_range()
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        total_purchases = queryset.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        
        serializer = ReportPurchaseSerializer(queryset, many=True)
        return response.Response({
            'total_purchases': total_purchases,
            'purchases': serializer.data
        })

class ExpensesReportAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        queryset = Expense.objects.filter(shop=shop).order_by('-date')
        start_date, end_date = self.get_date_range()
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        total_expenses = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        
        serializer = ReportExpenseSerializer(queryset, many=True)
        return response.Response({
            'total_expenses': total_expenses,
            'expenses': serializer.data
        })

class PricingReportAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        queryset = Product.objects.filter(shop=shop)
        serializer = ReportProductPricingSerializer(queryset, many=True)
        return response.Response(serializer.data)

class DisposalReportAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        # Filter stock movements for this shop (via product->shop or branch->shop)
        # Assuming product->shop is safest
        queryset = StockMovement.objects.filter(product__shop=shop, movement_type__in=['DISPOSAL', 'DAMAGED', 'EXPIRED']).order_by('-created_at')
        
        start_date, end_date = self.get_date_range()
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        serializer = ReportStockMovementSerializer(queryset, many=True)
        return response.Response(serializer.data)

class IncomeStatementAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
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
        
        return response.Response({
            'total_income': total_sales,
            'total_cogs': total_purchases,
            'gross_profit': total_sales - total_purchases,
            'total_expenses': total_expenses,
            'net_profit': (total_sales - total_purchases) - total_expenses
        })

class CashflowAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
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
        
        inflow = total_sales
        outflow = total_purchases + total_expenses
        
        return response.Response({
            'inflow': inflow,
            'outflow': outflow,
            'net_cashflow': inflow - outflow
        })

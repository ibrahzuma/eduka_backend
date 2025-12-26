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
from django.utils import timezone # Added timezone
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

    def get_summary_stats(self, queryset, date_field='created_at', sum_field='total_amount', date_transform=True):
        today = timezone.now().date()
        periods = {
            'today': today,
            'week': today - datetime.timedelta(days=7),
            'month': today - datetime.timedelta(days=30),
            'year': today - datetime.timedelta(days=365)
        }
        
        data = {}
        lookup_suffix = "__date__gte" if date_transform else "__gte"
        for key, start_date in periods.items():
            filter_kwargs = {f"{date_field}{lookup_suffix}": start_date}
            qs = queryset.filter(**filter_kwargs)
            
            if sum_field:
                total = qs.aggregate(Sum(sum_field))[f'{sum_field}__sum'] or 0
            else:
                total = 0 # or count?
                
            count = qs.count()
            data[key] = {
                'total': total,
                'count': count
            }
        return data

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

class SalesSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        base_qs = Sale.objects.filter(shop=shop)
        data = self.get_summary_stats(base_qs, date_field='created_at', sum_field='total_amount')
        return response.Response(data)

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

    def post(self, request):
        shop = self.get_shop()
        if not shop:
            return response.Response({'error': 'No shop associated'}, status=400)
            
        serializer = ReportExpenseSerializer(data=request.data)
        if serializer.is_valid():
            # Determine Branch
            branch = None
            if getattr(request.user, 'branch', None):
                 branch = request.user.branch
            elif hasattr(request.user, 'employee_profile') and request.user.employee_profile.branch:
                 branch = request.user.employee_profile.branch
            else:
                 # Default to Main Branch for Owner
                 if hasattr(shop, 'branches'):
                     branch = shop.branches.filter(is_main=True).first()
            
            if not branch:
                 return response.Response({'error': 'No active branch found for expense.'}, status=400)

            serializer.save(shop=shop, branch=branch)
            return response.Response(serializer.data, status=201)
        return response.Response(serializer.errors, status=400)

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

# New Summary Views
class PurchasesSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        qs = PurchaseOrder.objects.filter(shop=shop)
        data = self.get_summary_stats(qs, date_field='created_at', sum_field='total_cost')
        return response.Response(data)

class ExpensesSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        qs = Expense.objects.filter(shop=shop)
        # Expense uses 'date' (DateField), so no __date transform needed
        data = self.get_summary_stats(qs, date_field='date', sum_field='amount', date_transform=False)
        return response.Response(data)

class DisposalSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        # Disposal is StockMovement with type DISPOSAL or DAMAGED or EXPIRED
        qs = StockMovement.objects.filter(
            branch__shop=shop, 
            movement_type__in=['DISPOSAL', 'DAMAGED', 'EXPIRED']
        )
        # We need value. StockMovement doesn't have value field.
        # We need to annotate value = quantity_change (abs) * product__cost_price
        # Note: quantity_change is negative for reductions.
        from django.db.models import F
        from django.db.models.functions import Abs
        qs = qs.annotate(
            val=Abs(F('quantity_change')) * F('product__cost_price')
        )
        # StockMovement has created_at (DateTime)
        data = self.get_summary_stats(qs, date_field='created_at', sum_field='val')
        return response.Response(data)

class PricingSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        # Product has created_at (DateTime)
        qs = Product.objects.filter(shop=shop)
        data = self.get_summary_stats(qs, date_field='created_at', sum_field='selling_price')
        return response.Response(data)

class IncomeSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        
        # Income = Sales - Purchases - Expenses
        sales_data = self.get_summary_stats(Sale.objects.filter(shop=shop), 'created_at', 'total_amount')
        purchases_data = self.get_summary_stats(PurchaseOrder.objects.filter(shop=shop), 'created_at', 'total_cost')
        # Expenses need date_transform=False
        expenses_data = self.get_summary_stats(Expense.objects.filter(shop=shop), 'date', 'amount', date_transform=False)
        
        income_data = {}
        for key in ['today', 'week', 'month', 'year']:
            s = sales_data[key]['total']
            p = purchases_data[key]['total']
            e = expenses_data[key]['total']
            income_data[key] = {
                'total': s - p - e, # Net Profit
                'sales': s,
                'cogs': p,
                'expenses': e
            }
        return response.Response(income_data)

class CashflowSummaryAPIView(ReportBaseView):
    def get(self, request):
        shop = self.get_shop()
        if not shop: return response.Response({'error': 'No shop associated'}, status=400)
        
        sales_data = self.get_summary_stats(Sale.objects.filter(shop=shop), 'created_at', 'total_amount')
        purchases_data = self.get_summary_stats(PurchaseOrder.objects.filter(shop=shop), 'created_at', 'total_cost')
        expenses_data = self.get_summary_stats(Expense.objects.filter(shop=shop), 'date', 'amount', date_transform=False)
        
        cashflow_data = {}
        for key in ['today', 'week', 'month', 'year']:
            inflow = sales_data[key]['total']
            outflow = purchases_data[key]['total'] + expenses_data[key]['total']
            cashflow_data[key] = {
                'net_cashflow': inflow - outflow,
                'inflow': inflow,
                'outflow': outflow
            }
        return response.Response(cashflow_data)

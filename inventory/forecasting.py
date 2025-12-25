from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from sales.models import SaleItem

class SalesForecaster:
    def predict_daily_usage(self, product, shop, days=30):
        """
        Calculates the average daily usage of a product over the last X days.
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # Filter sales for this product in this shop (across all branches or specific logic?)
        # As SaleItem doesn't directly link to Shop, we filter via Sale -> Shop
        total_sold = SaleItem.objects.filter(
            product=product,
            sale__shop=shop,
            sale__created_at__range=(start_date, end_date)
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0

        return total_sold / days

    def predict_runout_date(self, stock):
        """
        Predicts the date when stock will run out.
        Returns: (date, days_left, status)
        """
        daily_usage = self.predict_daily_usage(stock.product, stock.branch.shop)
        
        if daily_usage <= 0:
            return None, None, 'Stagnant'

        days_left = stock.quantity / daily_usage
        
        # Cap at specific reasonable limits or just return raw
        runout_date = timezone.now() + timedelta(days=days_left)
        
        status = 'Safe'
        if days_left <= 3:
            status = 'Critical'
        elif days_left <= 7:
            status = 'Low'
            
        return runout_date, int(days_left), status

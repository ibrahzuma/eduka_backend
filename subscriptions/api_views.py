from rest_framework import views, permissions, response, serializers
from .models import SubscriptionPlan

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    price_display = serializers.SerializerMethodField()
    cycle = serializers.SerializerMethodField()
    display_price = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'slug', 'description', 'features', 'price_display', 'cycle', 'display_price']
        
    def get_cycle(self, obj):
        if obj.price_daily > 0: return 'daily'
        if obj.price_weekly > 0: return 'weekly'
        if obj.price_monthly > 0: return 'monthly'
        if obj.price_quarterly > 0: return 'quarterly'
        if obj.price_biannually > 0: return 'biannually'
        if obj.price_yearly > 0: return 'yearly'
        return 'monthly' # Fallback
        
    def get_price_display(self, obj):
        # Return the actual price value for the active cycle
        cycle = self.get_cycle(obj)
        if cycle == 'daily': return obj.price_daily
        if cycle == 'weekly': return obj.price_weekly
        if cycle == 'monthly': return obj.price_monthly
        if cycle == 'quarterly': return obj.price_quarterly
        if cycle == 'biannually': return obj.price_biannually
        if cycle == 'yearly': return obj.price_yearly
        return 0
        
    def get_display_price(self, obj):
        # Formatted string e.g. "1,000 / Day"
        price = self.get_price_display(obj)
        cycle = self.get_cycle(obj)
        
        cycle_labels = {
            'daily': 'Day',
            'weekly': 'Week',
            'monthly': 'Month',
            'quarterly': '3 Months',
            'biannually': '6 Months',
            'yearly': 'Year'
        }
        
        cycle_label = cycle_labels.get(cycle, cycle.title())
        return f"{price:,.0f} / {cycle_label}"

class SubscriptionPlanListView(views.APIView):
    permission_classes = [permissions.AllowAny] # Publicly accessible for landing page 

    def get(self, request):
        # Exclude Free Trial (case insensitive)
        plans = SubscriptionPlan.objects.filter(is_active=True).exclude(name__icontains='Trial')
        
        # Helper to determine sort order
        def get_sort_key(plan):
            if plan.price_daily > 0: return 1
            if plan.price_weekly > 0: return 2
            if plan.price_monthly > 0: return 3
            if plan.price_quarterly > 0: return 4
            if plan.price_biannually > 0: return 5
            if plan.price_yearly > 0: return 6
            return 7
            
        # Sort in Python
        sorted_plans = sorted(plans, key=get_sort_key)
        
        serializer = SubscriptionPlanSerializer(sorted_plans, many=True)
        return response.Response(serializer.data)

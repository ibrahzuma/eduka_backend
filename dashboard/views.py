from django.shortcuts import render
import django.http # Added for HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import TemplateView
from shops.models import Shop
from sales.models import Sale
from inventory.models import Stock
from django.db.models import Sum
from purchase.models import PurchaseOrder
from django.utils import timezone
from datetime import timedelta
from django.db import models # Added for aggregation
from .models import Notification

class DashboardTemplateView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            from django.shortcuts import redirect
            return redirect('superuser_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check GET parameters first, default to 'today'
        date_range = self.request.GET.get('date_range', 'today')
        return self.calculate_stats(context, date_range)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # Handle POST if standard form submission is used
        date_range = request.POST.get('date_range', 'today')
        context = self.calculate_stats(context, date_range)
        return render(request, self.template_name, context)

    def calculate_stats(self, context, date_range):
        user = self.request.user
        today = timezone.now().date()
        shops = Shop.objects.none() # Initialize to prevent UnboundLocalError for Super Admins
        
        # Determine start date and label based on range
        if date_range == 'week':
            start_date = today - timedelta(days=7)
            period_label = "Last 7 Days"
        elif date_range == 'month':
            start_date = today - timedelta(days=30)
            period_label = "Last 30 Days"
        elif date_range == 'year':
            start_date = today - timedelta(days=365)
            period_label = "Last 365 Days"
        else: # today
            start_date = today
            period_label = "Today"
            
        context['selected_range'] = date_range
        context['period_label'] = period_label

        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            context['type'] = 'Global'
            context['total_shops'] = Shop.objects.count()
            # Global Sales
            context['total_sales_volume'] = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            context['sales_period'] = Sale.objects.filter(created_at__date__gte=start_date).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            # Global Purchases
            context['total_purchases_volume'] = PurchaseOrder.objects.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            context['purchases_period'] = PurchaseOrder.objects.filter(created_at__date__gte=start_date).aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            
            context['recent_sales'] = Sale.objects.order_by('-created_at')[:5]
        else:
            context['type'] = 'Tenant'
            
            # Identify Shops
            if getattr(user, 'role', None) == 'EMPLOYEE':
                # Employee belongs to a shop
                shops = Shop.objects.filter(id=user.shop_id) if user.shop_id else Shop.objects.none()
            else:
                # Owner owns shops
                shops = Shop.objects.filter(owner=user)

            context['total_shops'] = shops.count()
            
            # Tenant Sales
            sales = Sale.objects.filter(shop__in=shops)
            
            # If Employee, further filter by cashier
            if getattr(user, 'role', None) == 'EMPLOYEE':
                sales = sales.filter(cashier=user)

            context['total_sales_volume'] = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            context['sales_period'] = sales.filter(created_at__date__gte=start_date).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            # Tenant Purchases (Generally employees don't see purchases unless role allows, but we'll filter similarly or hide)
            # For now, let's assume employees shouldn't see sensitive purchase data or just filter by shop
            # If we strictly follow "only show his staff" (stuff), maybe hide purchases? 
            # Letting it show shop purchases for now but could be restricted.
            # Tenant Purchases
            if getattr(user, 'role', None) == 'EMPLOYEE':
                 purchases = PurchaseOrder.objects.none() 
            else:
                purchases = PurchaseOrder.objects.filter(shop__in=shops)

            context['total_purchases_volume'] = purchases.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            context['purchases_period'] = purchases.filter(created_at__date__gte=start_date).aggregate(Sum('total_cost'))['total_cost__sum'] or 0
            
            context['low_stock_items'] = Stock.objects.filter(branch__shop__in=shops, quantity__lte=5).count()
            context['recent_sales'] = sales.order_by('-created_at')[:5]
            
            # Branches Count (Single Shop)
            if shops.exists():
                context['total_branches'] = shops.first().branches.count()
                
            # Top Cashier Logic
            try:
                # Filter sales for period (using 'sales_period' logic implicitly via sales & start_date)
                period_sales = sales.filter(created_at__date__gte=start_date)
                top_cashier_data = period_sales.values('cashier__username', 'cashier__first_name', 'cashier__last_name').annotate(
                    total=Sum('total_amount')
                ).order_by('-total').first()
                
                if top_cashier_data:
                    name = f"{top_cashier_data['cashier__first_name']} {top_cashier_data['cashier__last_name']}".strip()
                    context['top_cashier'] = {
                        'name': name if name else top_cashier_data['cashier__username'],
                        'amount': top_cashier_data['total']
                    }
            except Exception as e:
                print(f"Error calculating top cashier: {e}")
                pass
        
        # Get Subscription Status (Safe Mode)
        context['days_left'] = 0 # Default to 0 (expired/immediate action)
        context['subscription_status'] = 'EXPIRED'
        context['has_subscription'] = False
        
        if shops.exists():
            shop = shops.first()
            try:
                # Accessing shop.subscription raises DoesNotExist if missing
                sub = shop.subscription
                
                context['subscription'] = sub
                context['has_subscription'] = True
                context['subscription_status'] = sub.status
                
                if sub.end_date:
                    delta = sub.end_date - timezone.now()
                    days_left = delta.days
                    
                    # If subscription is technically active but less than 24h remain, days_left is 0.
                    # This should NOT be considered expired if end_date is in the future.
                    if sub.end_date <= timezone.now():
                         context['days_left'] = 0
                         context['subscription_status'] = 'EXPIRED'
                    else:
                         context['days_left'] = max(0, days_left)
                         # Do NOT override status if it's already ACTIVE/TRIAL
                         if context['subscription_status'] not in ['ACTIVE', 'TRIAL']:
                             context['subscription_status'] = 'EXPIRED'
                else:
                    context['days_left'] = 0
            except Exception:
                pass # Subscription does not exist

            # Fallback: Check Shop Registration Date for "Hidden" Trial
            if not context['has_subscription']:
                # Calculate days since registration
                days_since_reg = (timezone.now() - shop.created_at).days
                
                if days_since_reg < 7:
                    # User is within 7-day window, grant virtual trial status
                    context['has_subscription'] = True
                    context['subscription_status'] = 'TRIAL'
                    context['days_left'] = 7 - days_since_reg
                    # Mock a plan name for the template
                    class MockPlan:
                        name = "Free Trial"
                    class MockSub:
                        plan = MockPlan()
                    context['subscription'] = MockSub()
                else:
                    # Expired and No DB Record
                    class MockPlan:
                        name = "Free Tier"
                    class MockSub:
                        plan = MockPlan()
                    context['subscription'] = MockSub()

        # Calculate Banner Visibility (Backend Logic for Safety)
        if user.role == 'EMPLOYEE':
            context['show_subscription_banner'] = False
        else:
            context['show_subscription_banner'] = (
                context['days_left'] <= 7 or 
                context['subscription_status'] == 'EXPIRED' or 
                not context['has_subscription']
            )
        
        return context

class SuperUserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/superuser_dashboard.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Global Metrics
        context['total_shops'] = Shop.objects.count()
        context['total_users'] = Shop.objects.aggregate(total=models.Count('owner'))['total'] or 0 # Approx (owners)
        context['total_revenue'] = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Subscriptions (Mock or Real)
        from subscriptions.models import ShopSubscription
        context['recent_subscriptions'] = ShopSubscription.objects.select_related('shop', 'plan').order_by('-created_at')[:10]
        
        # Recent Shops
        context['recent_shops'] = Shop.objects.select_related('owner').order_by('-created_at')[:10]
        
        return context

    def post(self, request, *args, **kwargs):
        action_type = request.POST.get('action_type')
        from django.contrib import messages
        from django.shortcuts import redirect
        
        if action_type == 'toggle_status':
            shop_id = request.POST.get('shop_id')
            new_status = request.POST.get('status')
            
            try:
                shop = Shop.objects.get(id=shop_id)
                # Ensure subscription exists
                if hasattr(shop, 'subscription'):
                    sub = shop.subscription
                    sub.status = new_status
                    sub.save()
                    messages.success(request, f"Shop '{shop.name}' status updated to {new_status}.")
                else:
                    # Create default trial subscription if missing?
                    messages.warning(request, "Shop does not have a subscription plan to modify.")
            except Shop.DoesNotExist:
                messages.error(request, "Shop not found.")
                
        return redirect('superuser_dashboard')

class SuperUserCRMView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/superuser_crm.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from subscriptions.models import ShopSubscription, SubscriptionPayment
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta

        # 1. Pipeline Stats
        total_shops = Shop.objects.count()
        context['total_shops'] = total_shops
        context['active_paid'] = ShopSubscription.objects.filter(status='ACTIVE').count()
        context['active_trials'] = ShopSubscription.objects.filter(status='TRIAL').count()
        context['expired'] = ShopSubscription.objects.filter(status='EXPIRED').count()

        # 2. Revenue (MRR Estimation)
        # Assuming last 30 days of completed payments as monthly revenue proxy
        last_30_days = timezone.now() - timedelta(days=30)
        context['revenue_30d'] = SubscriptionPayment.objects.filter(
            status='COMPLETED', 
            created_at__gte=last_30_days
        ).aggregate(total=Sum('amount'))['total'] or 0

        # 3. Customer List (Consolidated CRM View)
        # We want to see Shops + Owners + Subscription Status
        shops = Shop.objects.select_related('owner', 'subscription', 'subscription__plan').all().order_by('-created_at')
        
        # Add 'health' flag to objects in memory
        for shop in shops:
            if hasattr(shop, 'subscription'):
                sub = shop.subscription
                if sub.status == 'ACTIVE':
                    shop.health_status = 'Healthy'
                    shop.health_class = 'success'
                elif sub.status == 'TRIAL':
                    shop.health_status = 'In Trial'
                    shop.health_class = 'primary'
                else:
                    shop.health_status = 'Expired'
                    shop.health_class = 'danger'
            else:
                shop.health_status = 'No Plan'
                shop.health_class = 'warning'

        context['shops'] = shops[:20] # Limit to 20 for now
        
        # 4. Conversion Calculation
        total_ever_trial = ShopSubscription.objects.filter(Q(status='ACTIVE') | Q(status='TRIAL') | Q(status='EXPIRED')).count()
        conversion = (context['active_paid'] / total_ever_trial * 100) if total_ever_trial > 0 else 0
        context['conversion_rate'] = round(conversion, 1)

        return context

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/settings.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
             context['shop'] = self.request.user.shops.first()
        return context

    def post(self, request, *args, **kwargs):
        # Save Shop Details
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            shop = request.user.shops.first()
            
            shop.name = request.POST.get('shop_name', shop.name)
            shop.address = request.POST.get('address', shop.address)
            shop.website = request.POST.get('website', shop.website)
            shop.phone = request.POST.get('phone', shop.phone)
            shop.email = request.POST.get('email', shop.email)
            
        return redirect('superuser_dashboard')

class SuperUserShopListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/superuser_shops_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shops = Shop.objects.select_related('owner', 'subscription', 'subscription__plan').all().order_by('-created_at')
        
        # Simple Search
        query = self.request.GET.get('q')
        if query:
            shops = shops.filter(name__icontains=query)
            
        context['shops'] = shops
        return context
        
    def post(self, request, *args, **kwargs):
        action_type = request.POST.get('action_type')
        from django.contrib import messages
        from django.shortcuts import redirect
        
        if action_type == 'toggle_status':
            shop_id = request.POST.get('shop_id')
            new_status = request.POST.get('status')
            try:
                shop = Shop.objects.get(id=shop_id)
                if hasattr(shop, 'subscription'):
                    sub = shop.subscription
                    sub.status = new_status
                    sub.save()
                    messages.success(request, f"Shop '{shop.name}' status updated to {new_status}.")
            except Shop.DoesNotExist:
                messages.error(request, "Shop not found.")
                
        return redirect('superuser_shop_list')


from django.views.generic import CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .forms import SuperUserShopForm
from shops.models import Branch, ShopSettings

class SuperUserShopCreateView(LoginRequiredMixin, CreateView):
    model = Shop
    form_class = SuperUserShopForm
    template_name = 'dashboard/shop_form.html'
    success_url = reverse_lazy('superuser_shop_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create Defaults
        shop = self.object
        ShopSettings.objects.get_or_create(shop=shop)
        Branch.objects.create(shop=shop, name='Main Branch', address=shop.address or 'HQ', is_main=True)
        # Add basic subscription plan? For now, settings.plan default is TRIAL.
        from subscriptions.models import ShopSubscription, SubscriptionPlan
        # Find a default plan or create dummy
        plan = SubscriptionPlan.objects.first() # Risky if none
        if not plan:
            plan = SubscriptionPlan.objects.create(name='Trial', price=0, duration_days=14)
            
        ShopSubscription.objects.create(shop=shop, plan=plan, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=plan.duration_days), status='ACTIVE')
        
        return response

class SuperUserShopUpdateView(LoginRequiredMixin, UpdateView):
    model = Shop
    form_class = SuperUserShopForm
    template_name = 'dashboard/shop_form.html'
    success_url = reverse_lazy('superuser_shop_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class SuperUserShopDeleteView(LoginRequiredMixin, DeleteView):
    model = Shop
    template_name = 'dashboard/shop_confirm_delete.html'
    success_url = reverse_lazy('superuser_shop_list')
    context_object_name = 'shop'
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        owner = self.object.owner
        
        # 1. Restriction: Do not delete if owner is Superuser
        if owner.is_superuser:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, "Restricted: You cannot delete a shop owned by a Super Administrator.")
            return redirect('superuser_shop_list')

        # 2. Cleanup: Delete the User Account as well (if not superuser)
        # Assuming Tenant = User + Shop. 
        # Note: If User has other shops, this might be aggressive. 
        # But 'New Tenant' flow implies 1-to-1.
        # Check if owner has other shops
        if owner.shops.count() <= 1:
            owner.delete() # Shop deleted by Cascade
        else:
             self.object.delete() # Only delete the shop
             
        from django.contrib import messages
        messages.success(request, "Shop and associated Tenant account deleted successfully.")
        return django.http.HttpResponseRedirect(self.get_success_url())

from subscriptions.models import SubscriptionPlan
from .forms import SubscriptionPlanForm

class SubscriptionPlanListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/subscription_plan_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = SubscriptionPlan.objects.all().order_by('price_monthly')
        return context

class SubscriptionPlanCreateView(LoginRequiredMixin, CreateView):
    model = SubscriptionPlan
    form_class = SubscriptionPlanForm
    template_name = 'dashboard/subscription_plan_form.html'
    success_url = reverse_lazy('superuser_plan_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class SubscriptionPlanUpdateView(LoginRequiredMixin, UpdateView):
    model = SubscriptionPlan
    form_class = SubscriptionPlanForm
    template_name = 'dashboard/subscription_plan_form.html'
    success_url = reverse_lazy('superuser_plan_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class SubscriptionPlanDeleteView(LoginRequiredMixin, DeleteView):
    model = SubscriptionPlan
    template_name = 'dashboard/subscription_plan_confirm_delete.html'
    success_url = reverse_lazy('superuser_plan_list')
    context_object_name = 'plan'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

from .models import GlobalSettings
from .forms import GlobalSettingsForm

class SuperUserGlobalSettingsView(LoginRequiredMixin, UpdateView):
    model = GlobalSettings
    form_class = GlobalSettingsForm
    template_name = 'dashboard/global_settings.html'
    success_url = reverse_lazy('superuser_settings')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return GlobalSettings.load()


from .forms import BroadcastForm

class SuperUserBroadcastView(LoginRequiredMixin, FormView):
    template_name = 'dashboard/broadcast_form.html'
    form_class = BroadcastForm
    success_url = reverse_lazy('superuser_broadcast')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        title = form.cleaned_data['title']
        message = form.cleaned_data['message']
        link = form.cleaned_data['link']
        send_email = form.cleaned_data['send_email']
        
        # Get all shop owners (distinct users who own a shop)
        recipients = Shop.objects.exclude(owner__isnull=True).values_list('owner', flat=True).distinct()
        
        # Create Notifications
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        notifications = []
        for user_id in recipients:
            notifications.append(Notification(
                recipient_id=user_id,
                verb=title,
                message=message,
                link=link
            ))
        
        Notification.objects.bulk_create(notifications)
        
        from django.contrib import messages
        messages.success(self.request, f"Broadcast sent successfully to {len(notifications)} users.")
        return super().form_valid(form)


class SuperUserUserListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/superuser_users_list.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        users = User.objects.all().order_by('-date_joined')
        
        # Search
        query = self.request.GET.get('q')
        if query:
            from django.db.models import Q
            users = users.filter(
                Q(username__icontains=query) | 
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
            
        # Filter Status/Role
        role = self.request.GET.get('role')
        if role:
            users = users.filter(role=role)

        context['users'] = users
        return context
        
    def post(self, request, *args, **kwargs):
        action_type = request.POST.get('action_type')
        from django.contrib import messages
        from django.shortcuts import redirect
        
        if action_type == 'toggle_status':
            user_id = request.POST.get('user_id')
            new_status = request.POST.get('status')
            User = get_user_model()
            
            try:
                user = User.objects.get(id=user_id)
                if user.is_superuser:
                    messages.error(request, "Cannot invoke action on Super Admins.")
                else:
                    user.is_active = (new_status == 'active')
                    user.save()
                    action = "Activated" if user.is_active else "Banned"
                    messages.success(request, f"User {user.username} has been {action}.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                
        return redirect('superuser_user_list')

class SuperUserUserDeleteView(LoginRequiredMixin, DeleteView):
    model = get_user_model()
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('superuser_user_list')
    context_object_name = 'object'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user.is_superuser:
             from django.contrib import messages
             messages.error(request, "Cannot delete Super Admin accounts.")
             return redirect('superuser_user_list')
        return super().delete(request, *args, **kwargs)


class ShopPricingView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/pricing_plans.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Show only active plans
        context['plans'] = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
        
        # Determine current plan
        if hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
            shop = self.request.user.shops.first()
            if hasattr(shop, 'subscription'):
                context['current_subscription'] = shop.subscription
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle Subscribe Logic Placeholders
        plan_id = request.POST.get('plan_id')
        cycle = request.POST.get('cycle')
        
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.info(request, f"Subscription upgrade to Plan ID {plan_id} ({cycle}) initiated. Payment Gateway not yet connected.")
        return redirect('shop_pricing')

from django.shortcuts import redirect

class LandingPageView(TemplateView):
    template_name = "landing.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass logic to template if needed, e.g. hide 'Login' button if authenticated
        return context

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/settings.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
             shop = self.request.user.shops.first()
             context['shop'] = shop
             # Pass Settings Explicitly
             from shops.models import ShopSettings
             settings_obj, _ = ShopSettings.objects.get_or_create(shop=shop)
             context['settings_obj'] = settings_obj
             
             # Pass Active Subscription Explicitly
             if hasattr(shop, 'subscription'):
                 context['active_subscription'] = shop.subscription
                 
        return context

    def post(self, request, *args, **kwargs):
        # Save Shop Details
        if hasattr(request.user, 'shops') and request.user.shops.exists():
            shop = request.user.shops.first()
            
            shop.name = request.POST.get('shop_name', shop.name)
            shop.address = request.POST.get('address', shop.address)
            shop.website = request.POST.get('website', shop.website)
            shop.phone = request.POST.get('phone', shop.phone)
            shop.email = request.POST.get('email', shop.email)
            
            if 'logo' in request.FILES:
                shop.logo = request.FILES['logo']
                
            shop.save()
        
        # Save theme to session (if still needed)
        if request.POST.get('theme'):
            request.session['theme'] = request.POST.get('theme')
        
        from django.contrib import messages
        messages.success(request, "Settings saved successfully!")
        return render(request, self.template_name, self.get_context_data())

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {}
        
        if getattr(user, 'role', None) == 'SUPER_ADMIN' or user.is_superuser:
            data['type'] = 'Global'
            data['total_shops'] = Shop.objects.count()
            data['total_sales_volume'] = Sale.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            
            # Subscription Revenue
            from subscriptions.models import SubscriptionPayment
            data['total_subscription_revenue'] = SubscriptionPayment.objects.filter(status='COMPLETED').aggregate(Sum('amount'))['amount__sum'] or 0
            
            data['recent_sales'] = Sale.objects.order_by('-created_at')[:5].values('id', 'total_amount', 'created_at')
        else:
            data['type'] = 'Tenant'
            shops = Shop.objects.filter(owner=user)
            data['total_shops'] = shops.count()
            sales = Sale.objects.filter(shop__in=shops)
            data['total_sales_volume'] = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            # Note: low_stock_items logic requires fix if used in API, keeping simple for now
            data['low_stock_items'] = Stock.objects.filter(branch__shop__in=shops, quantity__lte=5).count()
            data['recent_sales'] = sales.order_by('-created_at')[:5].values('id', 'total_amount', 'created_at')

        return Response(data)

class NotificationListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Fetch unread notifications first, then some read ones if needed, or just last 10
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:10]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        data = []
        for n in notifications:
            data.append({
                'id': n.id,
                'verb': n.verb,
                'message': n.message,
                'link': n.link,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
                'time_since': n.created_at  # We'll format this closer to "2m ago" in frontend or use helper here if needed
            })
            
        return Response({
            'unread_count': unread_count,
            'notifications': data
        })

class NotificationMarkReadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        notification_id = request.data.get('id')
        if notification_id:
            try:
                n = Notification.objects.get(id=notification_id, recipient=request.user)
                n.is_read = True
                n.save()
            except Notification.DoesNotExist:
                pass
        else:
            # Mark all as read
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
            
        return Response({'status': 'success'})

class PricingAPIView(APIView):
    permission_classes = [permissions.AllowAny] # Allow public access to pricing if needed, or IsAuthenticated

    def get(self, request):
        if request.user.is_superuser:
            plans = SubscriptionPlan.objects.all().order_by('price_monthly')
        else:
            plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_monthly')
            
        data = []
        for plan in plans:
            data.append({
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'price_daily': plan.price_daily,
                'price_weekly': plan.price_weekly,
                'price_monthly': plan.price_monthly,
                'price_quarterly': plan.price_quarterly,
                'price_biannually': plan.price_biannually,
                'price_yearly': plan.price_yearly,
                'max_shops': plan.max_shops,
                'max_users': plan.max_users,
                'max_products': plan.max_products,
                'features': plan.features, 
                'is_active': plan.is_active,  # Added this field for Admin UI
                'is_popular': plan.name == 'Pro' 
            })
        return Response(data)

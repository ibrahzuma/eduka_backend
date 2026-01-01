from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SubscriptionPlan, ShopSubscription, SubscriptionPayment
from .clickpesa_service import ClickPesaService
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone

class InitiatePaymentView(LoginRequiredMixin, View):
    def post(self, request):
        import json
        data = json.loads(request.body)
        
        plan_id = data.get('plan_id')
        phone = data.get('phone_number')
        
        if not plan_id or not phone:
            return JsonResponse({'success': False, 'message': 'Missing data'})

        shop = request.user.shops.first()
        if not shop:
            return JsonResponse({'success': False, 'message': 'No shop found'})
            
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)
        
        # Generate Reference
        # Generate Reference (Alphanumeric only)
        # Old: SUB-{shop.id}-{uuid} (invalid due to hyphens)
        # New: SUB{shop.id}{uuid} 
        reference = f"SUB{shop.id}X{uuid.uuid4().hex[:10].upper()}"
        cycle = data.get('cycle', 'monthly') # Default to monthly if missing
        
        # Determine Amount based on Cycle
        if cycle == 'daily':
            amount = plan.price_daily
        elif cycle == 'weekly':
            amount = plan.price_weekly
        elif cycle == 'monthly':
            amount = plan.price_monthly
        elif cycle == 'quarterly':
            amount = plan.price_quarterly
        elif cycle == 'biannually':
            amount = plan.price_biannually
        elif cycle == 'yearly':
            amount = plan.price_yearly
        else:
            amount = plan.price_monthly # Fallback
            
        if amount <= 0:
             return JsonResponse({'success': False, 'message': 'Invalid plan cycle selected'})
        
        # Create Pending Payment Record
        # We need a subscription object to link to. 
        # If one exists, use it, else create one temporarily or just link to shop logic later.
        # The model requires a subscription FK.
        subscription, created = ShopSubscription.objects.get_or_create(
             shop=shop,
             defaults={
                 'plan': plan, 
                 'end_date': request.user.date_joined, 
                 'status': 'EXPIRED',
                 'billing_cycle': cycle.upper()
             } 
        )
        # Update cycle if subscription existed
        if not created:
            subscription.billing_cycle = cycle.upper()
            subscription.plan = plan # Also update plan in case they switched
            subscription.save()
        
        payment = SubscriptionPayment.objects.create(
            subscription=subscription,
            amount=amount,
            transaction_id=reference,
            payment_method='CLICKPESA',
            status='PENDING'
        )
        
        # Call API
        try:
            service = ClickPesaService()
            result = service.initiate_ussd_push(phone, amount, reference)
            
            if result.get('success', False): 
                 return JsonResponse({
                     'success': True, 
                     'payment_id': payment.id,
                     'reference': reference,
                     'message': 'USSD Push Sent'
                 })
            else:
                 payment.status = 'FAILED'
                 payment.save()
                 error_msg = result.get('message', 'Unknown Error')
                 return JsonResponse({'success': False, 'message': f'Payment Gateway Error: {error_msg}'})
        except Exception as e:
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({'success': False, 'message': f'System Error: {str(e)}'})

class CheckPaymentStatusView(LoginRequiredMixin, View):
    def get(self, request, payment_id):
        payment = get_object_or_404(SubscriptionPayment, id=payment_id)
        
        service = ClickPesaService()
        # In real API, we query by Reference
        api_response = service.check_status(payment.transaction_id)
        
        # Parse API Response (Example Logic)
        # Assuming API returns status in 'status' field: 'SUCCESS', 'PENDING', 'FAILED'
        # Adjust parsing based on actual documentation response
        api_status = api_response.get('status', '').upper()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Payment Status Check for {payment_id}: {api_status} (Ref: {payment.transaction_id})")
        
        # Enhanced Status Check
        SUCCESS_STATUSES = ['SUCCESS', 'COMPLETED', 'PAID', 'SUCCESSFUL']
        FAILED_STATUSES = ['FAILED', 'CANCELLED', 'REJECTED']

        if api_status in SUCCESS_STATUSES:
            payment.status = 'COMPLETED'
            payment.save()
            
            # Activate Subscription
            sub = payment.subscription
            sub.status = 'ACTIVE'
            from django.utils import timezone
            from datetime import timedelta
            
            # Reset end_date if expired, or extend if active
            now = timezone.now()
            start_date = now if sub.end_date < now else sub.end_date
            
            cycle = sub.billing_cycle.upper()
            if cycle == 'DAILY':
                days = 1
            elif cycle == 'WEEKLY':
                days = 7
            elif cycle == 'QUARTERLY':
                days = 90
            elif cycle == 'BIANNUALLY':
                days = 180
            elif cycle == 'YEARLY':
                days = 365
            else:
                days = 30 # Default Monthly
                
            sub.end_date = start_date + timedelta(days=days)
            sub.save()
            
            return JsonResponse({'status': 'COMPLETED'})
            
        elif api_status in ['FAILED', 'CANCELLED']:
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({
                'status': 'FAILED', 
                'message': api_response.get('message', 'Transaction failed')
            })
            
        return JsonResponse({'status': 'PENDING'})

class SubscriptionStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.is_superuser:
            return Response({'is_valid': True, 'reason': 'superuser'})

        # Check User's Shop
        try:
            shop = user.shops.first() # related_name='shops'
            if shop:
                # 1. Check DB Subscription
                if hasattr(shop, 'subscription') and shop.subscription.is_valid():
                    return Response({'is_valid': True, 'reason': 'active_subscription', 'status': shop.subscription.status})
                
                # 2. Check Trial (7 Days)
                days_since_reg = (timezone.now() - shop.created_at).days
                if days_since_reg < 7:
                    return Response({'is_valid': True, 'reason': 'trial', 'days_left': 7 - days_since_reg})
                
                return Response({'is_valid': False, 'reason': 'expired'})
        except Exception as e:
            return Response({'is_valid': False, 'reason': 'error', 'details': str(e)})

        return Response({'is_valid': False, 'reason': 'no_shop'})

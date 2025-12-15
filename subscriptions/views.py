from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import SubscriptionPlan, ShopSubscription, SubscriptionPayment
from .clickpesa_service import ClickPesaService
import uuid

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
        reference = f"SUB-{shop.id}-{uuid.uuid4().hex[:8].upper()}"
        amount = plan.price_monthly # Default to monthly for now
        
        # Create Pending Payment Record
        # We need a subscription object to link to. 
        # If one exists, use it, else create one temporarily or just link to shop logic later.
        # The model requires a subscription FK.
        subscription, created = ShopSubscription.objects.get_or_create(
             shop=shop,
             defaults={'plan': plan, 'end_date': request.user.date_joined, 'status': 'EXPIRED'} # Dummy defaults
        )
        
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
        
        if api_status in ['SUCCESS', 'COMPLETED', 'PAID']:
            payment.status = 'COMPLETED'
            payment.save()
            
            # Activate Subscription
            sub = payment.subscription
            sub.status = 'ACTIVE'
            from django.utils import timezone
            from datetime import timedelta
            sub.end_date = timezone.now() + timedelta(days=30) # Monthly logic
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

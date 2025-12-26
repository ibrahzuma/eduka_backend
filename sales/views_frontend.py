from django.views.generic import ListView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Sale, SaleItem
from .forms import SaleForm
from inventory.models import Product
from django.db import transaction

class BaseShopView(LoginRequiredMixin):
    def get_shop(self):
        # 1. Check Owner Config
        if hasattr(self.request.user, 'shops') and self.request.user.shops.exists():
            return self.request.user.shops.first()
        
        # 2. Check Employee Config (Direct FK)
        if getattr(self.request.user, 'shop', None):
             return self.request.user.shop
             
        # 3. Fallback (Legacy)
        if hasattr(self.request.user, 'employee_profile'):
             return self.request.user.employee_profile.shop
             
        return None

class SaleListView(BaseShopView, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            return Sale.objects.filter(shop=shop).order_by('-created_at')
        return Sale.objects.none()

class SaleCreateView(BaseShopView, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/pos.html'
    success_url = reverse_lazy('sale_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['shop'] = self.get_shop()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_shop()
        if shop:
            from django.db.models import Sum, F
            # Get products with available stock
            # For simplicity, we sum stock across all branches for now, 
            # OR we should ideally filter by the logged-in user's branch if "Cashier" model had branch.
            # Assuming shop wide visibility for owner/admin.
            context['products'] = Product.objects.filter(shop=shop).annotate(
                stock_qty=Sum('stocks__quantity')
            )
        return context

    def form_valid(self, form):
        shop = self.get_shop()
        if not shop:
             messages.error(self.request, "No shop associated.")
             return self.form_invalid(form)
        
        # In a real POS, we'd handle items here. 
        # For this phase, we are just saving the 'header' or would need JS to submit items.
        # To make it functional simple: We will assume some items are passed or just save the header for now.
        # ideally we catch the JSON payload or POST data for items.
        
        with transaction.atomic():
            form.instance.shop = shop
            if hasattr(shop, 'branches') and shop.branches.exists():
                form.instance.branch = shop.branches.first()
            
            self.object = form.save()
            
            # Process SaleItems from hidden JSON input
            import json
            items_json = self.request.POST.get('items_json')
            if items_json:
                try:
                    items_data = json.loads(items_json)
                    for item in items_data:
                        product_id = item.get('id')
                        quantity = int(item.get('qty', 0))
                        price = float(item.get('price', 0))
                        
                        if product_id and quantity > 0:
                            product = Product.objects.get(id=product_id)
                            
                            # Apply Time-Based Pricing
                            from .utils_pricing import calculate_price
                            final_price, _, _ = calculate_price(product, shop)
                            
                            SaleItem.objects.create(
                                sale=self.object,
                                product=product,
                                quantity=quantity,
                                price=final_price # Use calculated price
                            )
                            
                            # SYNC: Deduct Stock
                            # Assuming Main Branch for simple setups or the branch selected on the form
                            branch = self.object.branch
                            if branch:
                                from inventory.models import Stock
                                stock_record = Stock.objects.filter(branch=branch, product=product).first()
                                if stock_record:
                                    stock_record.quantity -= quantity
                                    stock_record.save()
                                else:
                                    # Create negative stock record if not exists? Or just Log.
                                    # For robustness, we assume stock exists if it appeared in POS.
                                    pass
                            # Update total amount if handled here or trust frontend total passed? 
                            # Better: Calculate total from items to be safe
                    
                    # Recalculate sales total from items to ensure accuracy
                    self.object.total_amount = sum(item.price * item.quantity for item in self.object.items.all())
                    self.object.save()
                    
                    # SYNC: Create Notification
                    from dashboard.models import Notification
                    Notification.objects.create(
                        recipient=self.request.user, # Or Notify Admin?
                        verb="New Sale",
                        message=f"Sale #{self.object.id} completed. Total: {self.object.total_amount}",
                        link=f"/sales/" # Link to sale list
                    )
                    
                except json.JSONDecodeError:
                    messages.warning(self.request, "Error processing sale items.")
            
        messages.success(self.request, "Sale recorded successfully!")
        return super().form_valid(form)


class PlaceholderView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/placeholder.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.request.path.strip('/').replace('/', ' ').title()
        return context

class SaleCreditView(SaleListView):
    """Filter sales by credit payment method"""
    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            return Sale.objects.filter(shop=shop, payment_method='CREDIT').order_by('-created_at')
        return Sale.objects.none()

class SaleRecentView(SaleListView):
    """Latest 10 sales"""
    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            return Sale.objects.filter(shop=shop).order_by('-created_at')[:10]
        return Sale.objects.none()

from django.views.generic import DetailView
class SaleDetailView(BaseShopView, DetailView):
    model = Sale
    template_name = 'sales/invoice.html'
    context_object_name = 'sale'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            return Sale.objects.filter(shop=shop)
        return Sale.objects.none()

from .forms import SaleReturnForm, SaleSearchForm
from .models import SaleReturn, SaleReturnItem

class ReturnInwardsView(BaseShopView, TemplateView):
    template_name = 'sales/return_inwards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sale_id = self.request.GET.get('sale_id')
        
        context['search_form'] = SaleSearchForm(initial={'sale_id': sale_id} if sale_id else None)
        
        if sale_id:
            try:
                sale = Sale.objects.get(id=sale_id, shop=self.get_shop())
                context['sale'] = sale
                context['return_form'] = SaleReturnForm()
                # We could check previously returned items here to prevent double returns, 
                # but for now we trust the user or add complex logic later.
            except Sale.DoesNotExist:
                messages.error(self.request, f"Sale #{sale_id} not found.")
        
        return context

    def post(self, request, *args, **kwargs):
        sale_id = request.POST.get('sale_id')
        sale = Sale.objects.get(id=sale_id, shop=self.get_shop())
        
        form = SaleReturnForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                return_obj = form.save(commit=False)
                return_obj.sale = sale
                return_obj.processed_by = request.user
                return_obj.save()
                
                total_refund = 0
                items_returned = False
                
                # Iterate through Sale Items to check what is being returned
                # Expecting input names like "return_qty_{item_id}"
                for item in sale.items.all():
                    qty_key = f"return_qty_{item.id}"
                    return_qty = int(request.POST.get(qty_key, 0))
                    
                    if return_qty > 0:
                        if return_qty > item.quantity:
                             messages.error(request, f"Cannot return more than sold amount for {item.product.name}")
                             raise Exception("Invalid Return Quantity")
                        
                        items_returned = True
                        refund_amount = item.price * return_qty
                        total_refund += refund_amount
                        
                        # Create Return Item
                        SaleReturnItem.objects.create(
                            return_ref=return_obj,
                            product=item.product,
                            quantity=return_qty,
                            refund_price=item.price
                        )
                        
                        # SYNC: Restore Stock
                        # We try to find stock at the sale branch first
                        branch = sale.branch
                        if branch and item.product:
                            from inventory.models import Stock
                            stock, _ = Stock.objects.get_or_create(branch=branch, product=item.product)
                            stock.quantity += return_qty
                            stock.save()

                if not items_returned:
                     # Delete empty return wrapper if nothing selected (or error)
                     # But atomic transaction rollback handles exceptions. 
                     # Here we just didn't save items.
                     messages.warning(request, "No items selected for return.")
                     return redirect(f"{reverse_lazy('return_inwards')}?sale_id={sale_id}")

                return_obj.total_refund = total_refund
                return_obj.save()

                # Notify?
                from dashboard.models import Notification
                Notification.objects.create(
                    recipient=request.user,
                    verb="Sale Return",
                    message=f"Return processed for Sale #{sale.id}. Refund: {total_refund}",
                    link="#"
                )
                
            messages.success(request, f"Return processed successfully! Refund Amount: {total_refund}")
            return redirect('return_inwards')
            
        else:
             messages.error(request, "Error in return form.")
             return self.render_to_response(self.get_context_data())

    
from purchase.models import PurchaseOrder, PurchaseReturn, PurchaseReturnItem
from purchase.forms import PurchaseOrderSearchForm, PurchaseReturnForm

class ReturnOutwardsView(BaseShopView, TemplateView):
    template_name = 'sales/return_outwards.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        po_id = self.request.GET.get('po_id')
        
        context['search_form'] = PurchaseOrderSearchForm(initial={'po_id': po_id} if po_id else None)
        
        if po_id:
            try:
                # Assuming simple ID lookup for now, ideally scoped to shop
                po = PurchaseOrder.objects.get(id=po_id, shop=self.get_shop())
                context['po'] = po
                context['return_form'] = PurchaseReturnForm()
            except PurchaseOrder.DoesNotExist:
                messages.error(self.request, f"Purchase Order #{po_id} not found.")
        
        return context

    def post(self, request, *args, **kwargs):
        po_id = request.POST.get('po_id')
        po = PurchaseOrder.objects.get(id=po_id, shop=self.get_shop())
        
        form = PurchaseReturnForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                return_obj = form.save(commit=False)
                return_obj.purchase_order = po
                return_obj.processed_by = request.user
                return_obj.save()
                
                total_refund = 0
                items_returned = False
                
                # Iterate through PO Items
                for item in po.items.all():
                    qty_key = f"return_qty_{item.id}"
                    return_qty = int(request.POST.get(qty_key, 0))
                    
                    if return_qty > 0:
                        if return_qty > item.quantity:
                             messages.error(request, f"Cannot return more than purchased amount for {item.product.name}")
                             raise Exception("Invalid Return Quantity")
                        
                        items_returned = True
                        refund_amount = item.unit_cost * return_qty
                        total_refund += refund_amount
                        
                        # Create Return Item
                        PurchaseReturnItem.objects.create(
                            return_ref=return_obj,
                            product=item.product,
                            quantity=return_qty,
                            refund_amount=refund_amount
                        )
                        
                        # SYNC: REDUCE Stock (Sending goods back)
                        branch = po.branch
                        if branch and item.product:
                            from inventory.models import Stock
                            stock = Stock.objects.filter(branch=branch, product=item.product).first()
                            if stock:
                                stock.quantity -= return_qty
                                stock.save()
                
                if not items_returned:
                     messages.warning(request, "No items selected for return.")
                     return redirect(f"{reverse_lazy('return_outwards')}?po_id={po_id}")

                return_obj.total_refund = total_refund
                return_obj.save()
                
            messages.success(request, f"Return processed successfully! Refund Claim: {total_refund}")
            return redirect('return_outwards')
            
        else:
             messages.error(request, "Error in return form.")
             return self.render_to_response(self.get_context_data())

class SaleDeleteView(BaseShopView, DeleteView):
    model = Sale
    template_name = 'sales/sale_confirm_delete.html'
    success_url = reverse_lazy('sale_list')
    context_object_name = 'sale'

    def get_queryset(self):
        shop = self.get_shop()
        if shop:
            return Sale.objects.filter(shop=shop)
        return Sale.objects.none()

    def dispatch(self, request, *args, **kwargs):
        # Restriction: Only Owner or Super Admin
        if not (request.user.role == 'OWNER' or request.user.is_superuser):
            messages.error(request, "Permission Denied: Only Owners can delete sales.")
            return redirect('sale_list')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Restore Stock logic
        with transaction.atomic():
            for item in self.object.items.all():
                if item.product and self.object.branch:
                    from inventory.models import Stock
                    stock = Stock.objects.filter(branch=self.object.branch, product=item.product).first()
                    if stock:
                        stock.quantity += item.quantity
                        stock.save()
            
            messages.success(request, f"Sale #{self.object.id} deleted and stock restored.")
            return super().delete(request, *args, **kwargs)

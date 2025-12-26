from django.utils import timezone
from inventory.models import HappyHour
from decimal import Decimal

def calculate_price(product, shop, current_time=None):
    """
    Calculates the selling price of a product considering active Happy Hour rules.
    Returns: (final_price, original_price, discount_applied_bool)
    """
    if current_time is None:
        current_time = timezone.localtime()

    original_price = product.selling_price
    
    # 1. Filter Active Happy Hours for this Shop
    # Logic: Match Time window AND Day of week AND (Product OR Category)
    
    current_time_only = current_time.time()
    current_weekday = str(current_time.weekday()) # 0=Mon
    
    active_promos = HappyHour.objects.filter(
        shop=shop,
        is_active=True,
        start_time__lte=current_time_only,
        end_time__gte=current_time_only
    )
    
    best_discount = Decimal('0.00')
    discount_applied = False
    
    for promo in active_promos:
        # Check Day
        days = promo.days_of_week.split(',')
        if current_weekday not in days:
            continue
            
        # Check Product Scope
        is_applicable = False
        if promo.products.filter(id=product.id).exists():
            is_applicable = True
        elif product.category and promo.categories.filter(id=product.category.id).exists():
            is_applicable = True
            
        if is_applicable:
            if promo.discount_percent > best_discount:
                best_discount = promo.discount_percent
                discount_applied = True
                
    if discount_applied:
        discount_amount = original_price * (best_discount / 100)
        final_price = original_price - discount_amount
        return final_price, original_price, True
        
    return original_price, original_price, False

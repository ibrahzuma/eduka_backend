from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from .models import Shop
from inventory.models import Product, Stock

class PublicShopView(ListView):
    model = Product
    template_name = 'shops/public_store.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        self.shop = get_object_or_404(Shop, slug=self.kwargs['slug'], public_visibility=True)
        return Product.objects.filter(shop=self.shop, is_public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shop'] = self.shop
        return context

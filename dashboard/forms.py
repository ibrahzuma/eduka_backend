from django import forms
from shops.models import Shop
from django.contrib.auth import get_user_model

User = get_user_model()

class SuperUserShopForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Shop Owner",
        help_text="Select the user who owns this shop."
    )

    class Meta:
        model = Shop
        fields = ['owner', 'name', 'address', 'phone', 'email', 'website', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

from subscriptions.models import SubscriptionPlan

class SubscriptionPlanForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPlan
        fields = [
            'name', 'slug', 'description', 
            'price_daily', 'price_weekly', 'price_monthly', 
            'price_quarterly', 'price_biannually', 'price_yearly',
            'features', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            'price_daily': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_weekly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_monthly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_quarterly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_biannually': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_yearly': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            'features': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from .models import GlobalSettings

class GlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = GlobalSettings
        fields = ['site_name', 'default_currency', 'support_email', 'trial_days', 'allow_registration', 'maintenance_mode']
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TZS'}),
            'support_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'trial_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'allow_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BroadcastForm(forms.Form):
    title = forms.CharField(
        max_length=255, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement Title'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Type your message here...'}),
        required=True
    )
    link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional Action Link'})
    )
    send_email = forms.BooleanField(
        required=False, 
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Send Email Copy"
    )

from django import forms
from django.contrib.auth import get_user_model
from shops.models import Branch # Added import

User = get_user_model()
from .models import Role

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Role Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
        }

class UserRegistrationForm(forms.ModelForm):
    business_name = forms.CharField(label="Business Name", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Business Name'}))
    business_type = forms.ChoiceField(label="Business Type", choices=[('Retail', 'Retail Shop'), ('Wholesale', 'Wholesale Shop'), ('Service', 'Service')], widget=forms.Select(attrs={'class': 'form-select'}))
    region = forms.CharField(label="Region", widget=forms.Select(choices=[
        ('', 'Select Region'),
        ('Arusha', 'Arusha'),
        ('Dar es Salaam', 'Dar es Salaam'),
        ('Dodoma', 'Dodoma'),
        ('Geita', 'Geita'),
        ('Iringa', 'Iringa'),
        ('Kagera', 'Kagera'),
        ('Katavi', 'Katavi'),
        ('Kigoma', 'Kigoma'),
        ('Kilimanjaro', 'Kilimanjaro'),
        ('Lindi', 'Lindi'),
        ('Manyara', 'Manyara'),
        ('Mara', 'Mara'),
        ('Mbeya', 'Mbeya'),
        ('Morogoro', 'Morogoro'),
        ('Mtwara', 'Mtwara'),
        ('Mwanza', 'Mwanza'),
        ('Njombe', 'Njombe'),
        ('Pemba North', 'Pemba North'),
        ('Pemba South', 'Pemba South'),
        ('Pwani', 'Pwani'),
        ('Rukwa', 'Rukwa'),
        ('Ruvuma', 'Ruvuma'),
        ('Shinyanga', 'Shinyanga'),
        ('Simiyu', 'Simiyu'),
        ('Singida', 'Singida'),
        ('Songwe', 'Songwe'),
        ('Tabora', 'Tabora'),
        ('Tanga', 'Tanga'),
        ('Unguja North', 'Unguja North'),
        ('Unguja South', 'Unguja South'),
        ('Unguja Urban/West', 'Unguja Urban/West'),
    ], attrs={'class': 'form-select'}))
    district = forms.CharField(label="District", widget=forms.Select(choices=[('', 'Select District')], attrs={'class': 'form-select'}))
    street = forms.CharField(label="Street / Area", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street / Area'}))

    password = forms.CharField(label="Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'business_name', 'business_type', 'region', 'district', 'street']
        labels = {
            'username': 'Owner Name',
            'email': 'Email Address',
            'phone': 'Phone Number',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class EmployeeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    assigned_role = forms.ModelChoiceField(queryset=Role.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}), empty_label="Select Role")
    branch = forms.ModelChoiceField(queryset=Branch.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select'}), empty_label="Select Branch")

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'assigned_role', 'branch', 'password']
        labels = {
            'username': 'Username (for Login)',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'assigned_role': 'Role',
            'branch': 'Branch',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (Optional)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
        }

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['branch'].queryset = shop.branches.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        # Always set as Employee type if created through this form
        user.role = 'EMPLOYEE'
        if commit:
            user.save()
        return user

class EmployeeEditForm(forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password (leave blank to keep current)'}))
    branch = forms.ModelChoiceField(queryset=Branch.objects.none(), required=False, widget=forms.Select(attrs={'class': 'form-select'}), empty_label="Select Branch")

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'assigned_role', 'branch']
        labels = {
            'username': 'Username (for Login)',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'assigned_role': 'Role',
            'branch': 'Branch',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email (Optional)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'assigned_role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['branch'].queryset = shop.branches.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user




class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'first_name', 'last_name', 'profile_picture']
        labels = {
            'username': 'Username',
            'email': 'Email Address',
            'phone': 'Phone Number',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'profile_picture': 'Profile Picture',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

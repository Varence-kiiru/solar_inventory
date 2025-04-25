from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from .models import (
    User,
    Product,
    PurchaseOrder,
    PurchaseOrderItem,
    Sale,
    SaleItem,
    Customer,
    Supplier,
    Location,
    Brand,
    ProductCategory,
    StockAdjustment,
    InventoryCount,
    InventoryCountItem,
    PaymentReceived,
    Warranty,
    WarrantyClaim,
    ProductImage,
    ProductSpecification,
    SystemSettings,
    Notification
)


# User Forms
class UserForm(forms.ModelForm):
    """Form for creating and editing users"""
    
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        required=False,
        help_text=_("Leave blank if not changing password.")
    )
    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'is_active', 'is_staff', 'is_sales_person', 'is_inventory_manager',
            'profile_image', 'department', 'employee_id'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 or password2:
            if password1 != password2:
                raise ValidationError(_("Passwords don't match"))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone',
            'password1', 'password2'
        ]


class UserProfileForm(forms.ModelForm):
    """Form for users to edit their own profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'profile_image'
        ]
        widgets = {
            'profile_image': forms.FileInput(),
        }

class SettingsForm(forms.ModelForm):
    """Form for system-wide settings"""
    
    class Meta:
        model = SystemSettings
        fields = [
            'company_name', 'company_address', 'company_phone', 'company_email', 
            'company_website', 'company_logo', 'tax_rate', 'currency_symbol',
            'low_stock_threshold', 'enable_email_notifications', 'default_payment_terms'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control'}),
            'company_logo': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100, 
                'step': 0.01
            }),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1
            }),
            'enable_email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def clean_tax_rate(self):
        """Validate tax rate is between 0 and 100"""
        tax_rate = self.cleaned_data.get('tax_rate')
        if tax_rate < 0 or tax_rate > 100:
            raise forms.ValidationError("Tax rate must be between 0 and 100")
        return tax_rate
    
    def clean_company_logo(self):
        """Validate company logo file size and type"""
        logo = self.cleaned_data.get('company_logo')
        if logo and hasattr(logo, 'size'):
            # Check file size (limit to 2MB)
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file too large (max 2MB)")
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            import os
            ext = os.path.splitext(logo.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError("Unsupported file extension. Use jpg, jpeg, png or gif.")
        
        return logo

# Product Forms
class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""

    # Add these fields to match your template
    tax_rate = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        required=False,
        help_text=_("Tax rate percentage")
    )
    discount_price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        help_text=_("Discounted price (if applicable)")
    )
    location = forms.CharField(
        max_length=100, 
        required=False,
        help_text=_("Storage location")
    )
    warranty_info = forms.CharField(
        max_length=200, 
        required=False,
        help_text=_("Warranty information")
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    remove_image = forms.BooleanField(required=False)
    
    # Rename this field to match the template
    min_stock_level = forms.IntegerField(
        min_value=0,
        required=False,
        help_text=_("Minimum stock level before reordering")
    )
    
    # Rename this field to match the template
    suppliers = forms.ModelMultipleChoiceField(
        queryset=Supplier.objects.all(),
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'description', 'category', 'brand', 'unit_price',
            'cost_price', 'quantity_in_stock', 'minimum_stock_level', 'supplier',
            'image', 'barcode', 'active', 'weight', 'dimensions', 'warranty_period',
            'is_featured', 'tags', 'tax_rate', 'discount_price', 'location',
            'warranty_info', 'notes', 'remove_image'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'min_stock_level': forms.NumberInput(attrs={'min': 0}),  # Changed field name
            'quantity_in_stock': forms.NumberInput(attrs={'min': 0}),
            'unit_price': forms.NumberInput(attrs={'min': 0.01, 'step': '0.01'}),
            'cost_price': forms.NumberInput(attrs={'min': 0.01, 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),  # Added
            'discount_price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),  # Added
            'weight': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
            'dimensions': forms.TextInput(attrs={'placeholder': 'L x W x H'}),
            'warranty_period': forms.NumberInput(attrs={'min': 0}),
            'warranty_info': forms.Textarea(attrs={'rows': 3}),  # Added
            'notes': forms.Textarea(attrs={'rows': 3}),  # Added
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, tag3'}),
            'image': forms.FileInput(),
        }

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if self.instance.pk is None:  # New product
            if Product.objects.filter(sku=sku).exists():
                raise ValidationError(_("This SKU is already in use"))
        else:  # Existing product
            if Product.objects.filter(sku=sku).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("This SKU is already in use"))
        return sku

    def clean_barcode(self):
        barcode = self.cleaned_data.get('barcode')
        if not barcode:
            return barcode

        if self.instance.pk is None:  # New product
            if Product.objects.filter(barcode=barcode).exists():
                raise ValidationError(_("This barcode is already in use"))
        else:  # Existing product
            if Product.objects.filter(barcode=barcode).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("This barcode is already in use"))
        return barcode


class ProductImageForm(forms.ModelForm):
    """Form for product images"""

    class Meta:
        model = ProductImage
        fields = ['image', 'caption', 'is_primary', 'display_order']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }


ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=3,
    can_delete=True
)


class ProductSpecificationForm(forms.ModelForm):
    """Form for product specifications"""
    
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }


ProductSpecificationFormSet = inlineformset_factory(
    Product,
    ProductSpecification,
    form=ProductSpecificationForm,
    extra=3,
    can_delete=True
)


class ProductSearchForm(forms.Form):
    """Form for searching products"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by name, SKU or barcode'),
            'class': 'form-control'
        })
    )
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        empty_label=_("All Brands"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label=_("All Suppliers"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    in_stock = forms.BooleanField(required=False)
    low_stock = forms.BooleanField(required=False)
    active = forms.BooleanField(required=False, initial=True)

class ProductBulkUpdateForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        label='Category'
    )
    brand = forms.ModelChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        label='Brand'
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        label='Supplier'
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label='Location'
    )
    unit_price = forms.DecimalField(
        required=False,
        label='Unit Price',
        decimal_places=2,
        min_value=0
    )
    cost_price = forms.DecimalField(
        required=False,
        label='Cost Price',
        decimal_places=2,
        min_value=0
    )
    tax_rate = forms.DecimalField(
        required=False,
        label='Tax Rate (%)',
        decimal_places=2,
        min_value=0,
        max_value=100
    )
    minimum_stock_level = forms.IntegerField(
        required=False,
        label='Minimum Stock Level',
        min_value=0
    )
    active = forms.BooleanField(
        required=False,
        label='Active',
        widget=forms.Select(choices=((None, '---'), (True, 'Active'), (False, 'Inactive')))
    )
    is_featured = forms.BooleanField(
        required=False,
        label='Featured',
        widget=forms.Select(choices=((None, '---'), (True, 'Yes'), (False, 'No')))
    )
    warranty_period = forms.IntegerField(
        required=False,
        label='Warranty Period (months)',
        min_value=0
    )

class ProductCategoryForm(forms.ModelForm):
    """Form for creating and editing product categories"""
    
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'parent', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa-tag'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude self from parent choices to prevent circular references
        if self.instance.pk:
            self.fields['parent'].queryset = ProductCategory.objects.exclude(
                pk=self.instance.pk
            ).exclude(
                parent=self.instance
            )


class BrandForm(forms.ModelForm):
    """Form for creating and editing brands"""
    
    class Meta:
        model = Brand
        fields = [
            'name', 'description', 'logo', 'website', 
            'contact_email', 'contact_phone', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Supplier Forms
class SupplierForm(forms.ModelForm):
    """Form for creating and editing suppliers"""
    
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address',
            'tax_id', 'website', 'payment_terms', 'lead_time_days',
            'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'lead_time_days': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class SupplierSearchForm(forms.Form):
    """Form for searching suppliers"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by name or contact'),
            'class': 'form-control'
        })
    )
    is_active = forms.BooleanField(required=False, initial=True)


# Purchase Order Forms
class PurchaseOrderForm(forms.ModelForm):
    """Form for creating and editing purchase orders"""

    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'order_date', 'expected_delivery_date',
            'shipping_cost', 'tax_amount', 'notes'
        ]
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'shipping_cost': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'tax_amount': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        order_date = cleaned_data.get('order_date')
        expected_delivery_date = cleaned_data.get('expected_delivery_date')
        
        if order_date and expected_delivery_date and expected_delivery_date < order_date:
            raise ValidationError(_("Expected delivery date cannot be before order date"))

        return cleaned_data


class PurchaseOrderItemForm(forms.ModelForm):
    """Form for purchase order line items"""

    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_cost', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'min': 0.01, 'step': '0.01', 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True
)


class PurchaseOrderReceiveForm(forms.ModelForm):
    """Form for receiving purchase orders"""

    class Meta:
        model = PurchaseOrder
        fields = ['received_date', 'notes']
        widgets = {
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class PurchaseOrderItemReceiveForm(forms.ModelForm):
    """Form for receiving purchase order items"""

    class Meta:
        model = PurchaseOrderItem
        fields = ['received_quantity', 'notes']
        widgets = {
            'received_quantity': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_received_quantity(self):
        received_quantity = self.cleaned_data.get('received_quantity')
        if received_quantity > self.instance.quantity:
            raise ValidationError(_("Received quantity cannot exceed ordered quantity"))
        return received_quantity


PurchaseOrderItemReceiveFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemReceiveForm,
    extra=0,
    can_delete=False
)


class PurchaseOrderSearchForm(forms.Form):
    """Form for searching purchase orders"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by order number'),
            'class': 'form-control'
        })
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label=_("All Suppliers"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + list(PurchaseOrder.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


# Customer Forms
class CustomerForm(forms.ModelForm):
    """Form for creating and editing customers"""

    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'address', 'tax_id', 
            'credit_limit', 'is_active', 'date_of_birth',
            'company_name', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'min': 0, 'step': '0.01', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class CustomerSearchForm(forms.Form):
    """Form for searching customers"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by name, email or phone'),
            'class': 'form-control'
        })
    )
    is_active = forms.BooleanField(required=False, initial=True)

# Sale Forms
class SaleForm(forms.ModelForm):
    """Form for creating and editing sales"""

    class Meta:
        model = Sale
        fields = [
            'customer', 'payment_method', 'paid', 'notes',
            'discount_percentage', 'tax_percentage', 'shipping_cost',
            'due_date', 'reference_number', 'is_proforma'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'discount_percentage': forms.NumberInput(attrs={
                'min': 0, 'max': 100, 'step': '0.01', 'class': 'form-control'
            }),
            'tax_percentage': forms.NumberInput(attrs={
                'min': 0, 'max': 100, 'step': '0.01', 'class': 'form-control'
            }),
            'shipping_cost': forms.NumberInput(attrs={
                'min': 0, 'step': '0.01', 'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'discount_percentage': _('Discount percentage (%)'),
            'tax_percentage': _('Tax percentage (%)'),
            'shipping_cost': _('Shipping cost'),
            'due_date': _('Required for credit sales'),
            'reference_number': _('Required for card/mobile payments'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make is_proforma a hidden field
        self.fields['is_proforma'].widget = forms.HiddenInput()
        
        # Set initial values based on payment method
        payment_method = self.initial.get('payment_method')
        if payment_method == Sale.CREDIT:
            self.initial['is_proforma'] = True
            self.initial['paid'] = False
            self.initial.setdefault('due_date', (timezone.now() + timedelta(days=30)).date())

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        customer = cleaned_data.get('customer')
        paid = cleaned_data.get('paid')
        due_date = cleaned_data.get('due_date')
        reference_number = cleaned_data.get('reference_number')
        is_proforma = cleaned_data.get('is_proforma')

        errors = {}

        # Credit sales validation
        if payment_method == Sale.CREDIT:
            if not customer:
                errors['customer'] = _('Credit sales require a customer.')
            
            # FIXED: Force paid to False for credit sales instead of raising error
            cleaned_data['paid'] = False
            
            if not due_date:
                errors['due_date'] = _('Credit sales require a due date.')
            
            # FIXED: Force is_proforma to True for credit sales
            cleaned_data['is_proforma'] = True

        # Card/Mobile payment validation
        if payment_method in [Sale.CARD, Sale.MOBILE] and not reference_number:
            errors['reference_number'] = _('Card and mobile payments require a reference number.')

        # FIXED: Force paid to False for proforma invoices instead of raising error
        if is_proforma:
            cleaned_data['paid'] = False

        if errors:
            raise forms.ValidationError(errors)

        return cleaned_data

class SaleItemForm(forms.ModelForm):
    """Form for sale items"""
    
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price', 'discount']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'quantity': forms.NumberInput(attrs={
                'min': 1, 'class': 'form-control quantity-input'
            }),
            'unit_price': forms.NumberInput(attrs={
                'min': 0, 'step': '0.01', 'class': 'form-control price-input'
            }),
            'discount': forms.NumberInput(attrs={
                'min': 0, 'step': '0.01', 'class': 'form-control discount-input'
            }),
        }

# Create a formset for sale items
SaleItemFormSet = forms.inlineformset_factory(
    Sale, 
    SaleItem, 
    form=SaleItemForm,
    extra=1, 
    can_delete=True
)



class ProformaConversionForm(forms.Form):
    """Form for converting proforma invoices to sales"""
    
    payment_method = forms.ChoiceField(
        choices=[
            (Sale.CASH, _('Cash')),
            (Sale.BANK, _('Bank Transfer')),
            (Sale.MOBILE, _('Mobile Money')),
            (Sale.CARD, _('Credit/Debit Card'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    reference_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Required for card/mobile payments")
    )
    
    amount_tendered = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        help_text=_("Amount received from customer")
    )
    
    change_amount = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
        help_text=_("Change given to customer")
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        help_text=_("Additional notes about the payment")
    )
    
    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        reference_number = cleaned_data.get('reference_number')
        
        # Card/Mobile payment validation
        if payment_method in [Sale.CARD, Sale.MOBILE] and not reference_number:
            raise ValidationError(_("Card and mobile payments require a reference number"))
            
        return cleaned_data


# Create the formset for sale items
SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=1,
    can_delete=True
)

class SaleSearchForm(forms.Form):
    """Form for searching sales"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by invoice number'),
            'class': 'form-control'
        })
    )
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label=_("All Customers"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_method = forms.ChoiceField(
        choices=[('', _('All Methods'))] + list(Sale.PAYMENT_METHOD_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    paid = forms.ChoiceField(
        choices=[
            ('', _('All')),
            ('paid', _('Paid')),
            ('unpaid', _('Unpaid')),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


# Payment Forms
class PaymentReceivedForm(forms.ModelForm):
    """Form for recording payments received"""
    
    class Meta:
        model = PaymentReceived
        fields = ['amount', 'payment_date', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': 0.01, 'step': '0.01', 'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, sale=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sale = sale
        
        if sale:
            # Calculate remaining amount
            total_paid = sum(payment.amount for payment in sale.payments.all())
            remaining = sale.total_amount - total_paid
            
            # Set initial amount to remaining balance
            self.fields['amount'].initial = remaining
            
            # Set max amount to remaining balance
            self.fields['amount'].widget.attrs['max'] = remaining
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        
        if self.sale:
            # Calculate remaining amount
            total_paid = sum(payment.amount for payment in self.sale.payments.all())
            remaining = self.sale.total_amount - total_paid
            
            if amount > remaining:
                raise ValidationError(_("Payment amount cannot exceed the remaining balance of %s") % remaining)
        
        return amount


# Stock Adjustment Forms
class StockAdjustmentForm(forms.ModelForm):
    """Form for stock adjustments"""
    
    class Meta:
        model = StockAdjustment
        fields = ['product', 'quantity', 'adjustment_type', 'reason', 'date', 'notes', 'reference_number']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'adjustment_type': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        adjustment_type = cleaned_data.get('adjustment_type')
        
        if product and quantity and adjustment_type == StockAdjustment.DECREASE:
            if quantity > product.quantity_in_stock:
                raise ValidationError(
                    _("Cannot decrease more than current stock. Current stock: %s") % product.quantity_in_stock
                )
        
        return cleaned_data

# Inventory Count Forms
class InventoryCountForm(forms.ModelForm):
    """Form for inventory counts"""
    
    class Meta:
        model = InventoryCount
        fields = ['count_date', 'notes', 'status']
        widgets = {
            'count_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class InventoryCountItemForm(forms.ModelForm):
    """Form for inventory count items"""
    
    class Meta:
        model = InventoryCountItem
        fields = ['product', 'system_quantity', 'counted_quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select', 'readonly': 'readonly'}),
            'system_quantity': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'counted_quantity': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control'}),
        }


InventoryCountItemFormSet = inlineformset_factory(
    InventoryCount,
    InventoryCountItem,
    form=InventoryCountItemForm,
    extra=0,
    can_delete=False
)


# Warranty Forms
class WarrantyForm(forms.ModelForm):
    """Form for product warranties"""
    
    class Meta:
        model = Warranty
        fields = ['warranty_start', 'warranty_end', 'serial_number', 'terms']
        widgets = {
            'warranty_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('warranty_start')
        end_date = cleaned_data.get('warranty_end')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError(_("Warranty end date cannot be before start date"))
        
        return cleaned_data


class WarrantyClaimForm(forms.ModelForm):
    """Form for warranty claims"""
    
    class Meta:
        model = WarrantyClaim
        fields = ['claim_date', 'description', 'status', 'resolution', 'resolved_date']
        widgets = {
            'claim_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'resolution': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'resolved_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        resolution = cleaned_data.get('resolution')
        resolved_date = cleaned_data.get('resolved_date')
        
        if status == 'resolved':
            if not resolution:
                raise ValidationError(_("Resolution is required when status is resolved"))
            if not resolved_date:
                raise ValidationError(_("Resolved date is required when status is resolved"))
        
        return cleaned_data


# System Settings Form
class SystemSettingsForm(forms.ModelForm):
    """Form for system settings"""
    
    class Meta:
        model = SystemSettings
        fields = [
            'company_name', 'company_address', 'company_phone',
            'company_email', 'company_website', 'company_logo',
            'tax_rate', 'currency_symbol', 'low_stock_threshold',
            'enable_email_notifications', 'default_payment_terms'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control'}),
            'company_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': '0.01', 'class': 'form-control'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'default_payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Report Forms
class DateRangeForm(forms.Form):
    """Form for date range selection in reports"""
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError(_("End date cannot be before start date"))
        
        return cleaned_data


class SalesReportForm(DateRangeForm):
    """Form for sales report filtering"""
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.all(),
        required=False,
        empty_label=_("All Customers"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    product_category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_method = forms.ChoiceField(
        choices=[('', _('All Methods'))] + list(Sale.PAYMENT_METHOD_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    group_by = forms.ChoiceField(
        choices=[
            ('day', _('Day')),
            ('week', _('Week')),
            ('month', _('Month')),
            ('product', _('Product')),
            ('category', _('Category')),
            ('customer', _('Customer')),
        ],
        initial='day',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class InventoryReportForm(forms.Form):
    """Form for inventory report filtering"""
    
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        required=False,
        empty_label=_("All Suppliers"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    show_zero_stock = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Show Zero Stock Items")
    )
    show_low_stock = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Show Low Stock Items")
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('name', _('Name')),
            ('stock', _('Stock Level')),
            ('value', _('Stock Value')),
            ('category', _('Category')),
        ],
        initial='stock',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProfitReportForm(DateRangeForm):
    """Form for profit report filtering"""
    
    product_category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    group_by = forms.ChoiceField(
        choices=[
            ('day', _('Day')),
            ('week', _('Week')),
            ('month', _('Month')),
            ('product', _('Product')),
            ('category', _('Category')),
        ],
        initial='day',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# Import/Export Forms
class ProductImportForm(forms.Form):
    """Form for importing products from CSV/Excel."""

    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label=_("Select a file"),
        help_text=_("Accepted formats: CSV, Excel (.xlsx)")
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Update existing products"),
        help_text=_("Update existing products if SKU matches")
    )
    skip_errors = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Skip rows with errors"),
        help_text=_("Ignore rows that contain errors during import")
    )


class CustomerImportForm(forms.Form):
    """Form for importing customers from CSV/Excel"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text=_("Accepted formats: CSV, Excel (.xlsx)")
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        help_text=_("Update existing customers if email matches")
    )


class SupplierImportForm(forms.Form):
    """Form for importing suppliers from CSV/Excel"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        help_text=_("Accepted formats: CSV, Excel (.xlsx)")
    )
    update_existing = forms.BooleanField(
        required=False,
        initial=True,
        help_text=_("Update existing suppliers if email matches")
    )


# Notification Forms
class NotificationForm(forms.ModelForm):
    """Form for creating notifications"""
    
    class Meta:
        model = Notification
        fields = ['user', 'title', 'message', 'priority', 'link']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'link': forms.TextInput(attrs={'class': 'form-control'}),
        }


class NotificationBulkForm(forms.Form):
    """Form for sending bulk notifications"""
    
    title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    link = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        help_text=_("Hold Ctrl/Cmd to select multiple users")
    )


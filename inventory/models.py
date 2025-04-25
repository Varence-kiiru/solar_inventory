from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import random
import string

class User(AbstractUser):
    """
    Custom user model with additional fields for role-based access control
    in the inventory management system.
    """
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', _("Enter a valid phone number"))]
    )
    is_sales_person = models.BooleanField(default=False)
    is_inventory_manager = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.get_full_name() or self.username
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_role_display(self):
        """Returns a string representation of the user's role(s)"""
        roles = []
        if self.is_superuser:
            roles.append("Admin")
        if self.is_staff:
            roles.append("Staff")
        if self.is_sales_person:
            roles.append("Sales")
        if self.is_inventory_manager:
            roles.append("Inventory")
        return ", ".join(roles) if roles else "User"


class TimestampModel(models.Model):
    """
    Abstract model for tracking creation and modification dates.
    All models in the system should inherit from this for audit purposes.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Brand(TimestampModel):
    """
    Product brand model for categorizing products by manufacturer.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Brand")
        verbose_name_plural = _("Brands")

    def __str__(self):
        return self.name
    
    @property
    def product_count(self):
        """Returns the number of products associated with this brand"""
        return self.products.count()

class Supplier(models.Model):
    """
    Supplier/Vendor model for tracking product sources and purchase orders.
    """

    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    lead_time_days = models.PositiveIntegerField(
        default=7, 
        help_text=_("Average lead time in days")
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        """Returns the total number of products linked to this supplier."""
        return self.product_set.count()

    @property
    def total_orders(self):
        """Returns the total number of purchase orders from this supplier."""
        return self.purchaseorder_set.count()

    @property
    def pending_orders(self):
        """Returns the number of pending purchase orders from this supplier."""
        return self.purchaseorder_set.filter(status='pending').count()

class ProductCategory(TimestampModel):
    """
    Product category model for organizing products into hierarchical categories.
    Limited to one level of nesting for simplicity.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField(max_length=50, blank=True, help_text=_("Font Awesome icon class"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def clean(self):
        if self.parent and self.parent.parent:
            raise ValidationError(_("Categories can only be nested one level deep"))
        if self.parent and self.parent == self:
            raise ValidationError(_("A category cannot be its own parent"))

    @property
    def product_count(self):
        """Returns the number of products in this category"""
        count = self.products.count()
        for child in self.children.all():
            count += child.products.count()
        return count


class Product(TimestampModel):
    """
    Inventory product model representing items in stock.
    Includes pricing, stock levels, and supplier information.
    """
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    quantity_in_stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    minimum_stock_level = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)]
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    last_restocked = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    active = models.BooleanField(default=True)
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True, 
        null=True,
        help_text=_("Weight in kg")
    )
    dimensions = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Format: LxWxH in cm")
    )
    warranty_period = models.PositiveIntegerField(
        default=0,
        help_text=_("Warranty period in months")
    )
    is_featured = models.BooleanField(default=False)
    tags = models.CharField(max_length=200, blank=True, help_text=_("Comma-separated tags"))

    class Meta:
        ordering = ['name']
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def needs_restock(self):
        """Returns True if stock level is at or below minimum"""
        return self.quantity_in_stock <= self.minimum_stock_level
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price > 0:
            return ((self.unit_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.quantity_in_stock * self.cost_price
    
    @classmethod
    def get_low_stock_products(cls, limit=None):
        """Class method to get low stock products efficiently"""
        queryset = cls.objects.filter(
            quantity_in_stock__lte=models.F('minimum_stock_level'),
            active=True
        ).order_by('quantity_in_stock')
        
        if limit:
            return queryset[:limit]
        return queryset

    def save(self, *args, **kwargs):
        if self.quantity_in_stock > 0 and not self.last_restocked:
            self.last_restocked = timezone.now().date()
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    """
    Additional product images model.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='additional_images'
    )
    image = models.ImageField(upload_to='products/')
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductSpecification(models.Model):
    """
    Technical specifications for products.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='specifications'
    )
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ['product', 'name']
        verbose_name = _("Product Specification")
        verbose_name_plural = _("Product Specifications")
    
    def __str__(self):
        return f"{self.name}: {self.value}"

class Customer(TimestampModel):
    """
    Customer model for tracking sales and customer information.
    """
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    date_of_birth = models.DateField(null=True, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile'
    )

    class Meta:
        ordering = ['name']
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name
    
    @property
    def total_purchases(self):
        """Calculate total amount spent by customer"""
        from django.db.models import Sum
        total = self.sales.aggregate(total=Sum('total_amount'))['total']
        return total or 0
    
    @property
    def last_purchase_date(self):
        """Get date of last purchase"""
        last_sale = self.sales.order_by('-sale_date').first()
        return last_sale.sale_date if last_sale else None


class PurchaseOrder(TimestampModel):
    """
    Purchase order model for tracking orders to suppliers.
    """
    PENDING = 'pending'
    RECEIVED = 'received'
    CANCELLED = 'cancelled'
    PARTIALLY_RECEIVED = 'partially_received'

    STATUS_CHOICES = [
        (PENDING, _('Pending')),
        (PARTIALLY_RECEIVED, _('Partially Received')),
        (RECEIVED, _('Received')),
        (CANCELLED, _('Cancelled')),
    ]

    order_number = models.CharField(
        max_length=20,
        unique=True, 
        blank=True,
        help_text=_("Auto-generated if left blank")
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders'
    )
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_purchase_orders'
    )
    received_date = models.DateField(null=True, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_purchase_orders'
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Automatically calculated from items")
    )

    class Meta:
        ordering = ['-order_date']
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        indexes = [
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.order_number} ({self.supplier})"

    def save(self, *args, **kwargs):
        # Generate order number if not provided
        if not self.order_number:
            last_po = PurchaseOrder.objects.order_by('-id').first()
            last_id = last_po.id if last_po else 0
            self.order_number = f"PO-{last_id + 1:06d}"

        # Update status based on received quantities
        if self.status != self.CANCELLED and self.id:  # Only for existing POs
            received_count = 0
            total_items = 0

            for item in self.items.all():
                total_items += 1
                if item.received_quantity == item.quantity:
                    received_count += 1
            
            if total_items > 0:
                if received_count == 0:
                    self.status = self.PENDING
                elif received_count == total_items:
                    self.status = self.RECEIVED
                    if not self.received_date:
                        self.received_date = timezone.now().date()
                else:
                    self.status = self.PARTIALLY_RECEIVED
        
        # Calculate total amount
        if self.id:  # Only for existing POs
            subtotal = sum(item.total_price for item in self.items.all())
            self.total_amount = subtotal + self.shipping_cost + self.tax_amount
            
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.expected_delivery_date and self.order_date and self.expected_delivery_date < self.order_date:
            raise ValidationError(_("Delivery date cannot be before order date"))
    
    @property
    def total_cost(self):
        """Calculate total cost including items, shipping and tax"""
        subtotal = sum(item.total_price for item in self.items.all())
        return subtotal + self.shipping_cost + self.tax_amount
    
    @property
    def is_overdue(self):
        """Check if the order is overdue"""
        return (
            self.status == self.PENDING and 
            self.expected_delivery_date < timezone.now().date()
        )
    
    @property
    def days_until_delivery(self):
        """Calculate days until expected delivery"""
        if self.expected_delivery_date:
            delta = self.expected_delivery_date - timezone.now().date()
            return delta.days
        return None


class PurchaseOrderItem(models.Model):
    """
    Purchase order line items representing products ordered from suppliers.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    received_quantity = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = _("Purchase Order Item")
        verbose_name_plural = _("Purchase Order Items")
        unique_together = ['purchase_order', 'product']
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
    
    @property
    def total_price(self):
        """Calculate total price for this line item"""
        return self.quantity * self.unit_cost
    
    @property
    def received_status(self):
        """Return status of received items"""
        if self.received_quantity == 0:
            return _("Not Received")
        elif self.received_quantity < self.quantity:
            return _("Partially Received")
        else:
            return _("Fully Received")
    
    def save(self, *args, **kwargs):
        if self.received_quantity > self.quantity:
            raise ValidationError(_("Received quantity cannot exceed ordered quantity"))
        super().save(*args, **kwargs)
        
        # Update parent purchase order status
        self.purchase_order.save()

from decimal import Decimal
from datetime import timedelta
from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ValidationError

class Sale(TimestampModel):
    """
    Sales transaction model for tracking customer purchases.
    """
    CASH = 'cash'
    CREDIT = 'credit'
    BANK = 'bank'
    MOBILE = 'mobile'
    CARD = 'card'

    PAYMENT_METHOD_CHOICES = [
        (CASH, _('Cash')),
        (CREDIT, _('Credit')),
        (BANK, _('Bank Transfer')),
        (MOBILE, _('Mobile Money')),
        (CARD, _('Credit/Debit Card'))
    ]

    # Sale status choices
    STATUS_DRAFT = 'draft'
    STATUS_COMPLETED = 'completed'
    STATUS_PROFORMA = 'proforma'
    STATUS_VOIDED = 'voided'
   
    STATUS_CHOICES = [
        (STATUS_DRAFT, _('Draft')),
        (STATUS_COMPLETED, _('Completed')),
        (STATUS_PROFORMA, _('Proforma')),
        (STATUS_VOIDED, _('Voided')),
    ]

    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text=_("Auto-generated if left blank")
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sales'
    )
    sale_date = models.DateTimeField(default=timezone.now)
    sales_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales'
    )
    paid = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        default=CASH
    )
    notes = models.TextField(blank=True)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        null=True,
        blank=True
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Automatically calculated from items")
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Required for credit sales")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )
    is_proforma = models.BooleanField(
        default=False,
        help_text=_("Whether this is a proforma invoice")
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Reference number for card/mobile payments")
    )
    amount_tendered = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Amount received from customer")
    )
    change_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("Change given to customer")
    )

    class Meta:
        ordering = ['-sale_date']
        verbose_name = _("Sale")
        verbose_name_plural = _("Sales")
        indexes = [
            models.Index(fields=['sale_date']),
            models.Index(fields=['paid']),
            models.Index(fields=['status']),
        ]
   
    def __str__(self):
        return f"{self.invoice_number}"
   
    def save(self, *args, **kwargs):
        # Generate invoice number if not provided
        if not self.invoice_number:
            last_id = Sale.objects.aggregate(max_id=models.Max('id'))['max_id'] or 0
            prefix = "PRO" if self.is_proforma or self.payment_method == self.CREDIT else "INV"
            self.invoice_number = f"{prefix}-{last_id + 1:06d}"

        # Calculate total amount for existing sales
        if self.id:
            self.total_amount = self.calculate_total_amount

        # FIXED: Handle credit sales logic properly
        if self.payment_method == self.CREDIT:
            self.is_proforma = True
            self.paid = False  # Credit sales must be unpaid initially
            self.status = self.STATUS_PROFORMA
            
            # Set default due date if not provided
            if not self.due_date:
                self.due_date = timezone.now().date() + timedelta(days=30)

        # Set appropriate status based on is_proforma and paid flags
        if self.is_proforma:
            self.status = self.STATUS_PROFORMA
            self.paid = False  # FIXED: Proforma invoices are always unpaid
        elif self.paid:
            self.status = self.STATUS_COMPLETED

        super().save(*args, **kwargs)

    def clean(self):
        # Credit sales validation
        if self.payment_method == self.CREDIT:
            if not self.customer:
                raise ValidationError(_("Credit sales require a customer"))
            
            # FIXED: Don't validate paid status for credit sales since we force it to False in save()
            if not self.due_date:
                raise ValidationError(_("Credit sales require a due date"))
        
        # Card/Mobile payment validation
        if self.payment_method in [self.CARD, self.MOBILE] and not self.reference_number:
            raise ValidationError(_("Card and mobile payments require a reference number"))
        
        # FIXED: Don't validate paid status for proforma invoices since we force it to False in save()
        if self.is_proforma and self.paid:
            self.paid = False  # Silently correct instead of raising error

    @property
    def calculate_total_amount(self):
        """Calculate total amount including discounts, taxes and shipping"""
        subtotal = sum(Decimal(item.total_price) for item in self.items.all())
        discount_amount = subtotal * (self.discount_percentage / Decimal(100))
        tax_amount = (subtotal - discount_amount) * (self.tax_percentage / Decimal(100))
        shipping = self.shipping_cost or Decimal(0)
        return subtotal - discount_amount + tax_amount + shipping

    @property
    def is_overdue(self):
        """Check if a credit sale is overdue"""
        return (
            self.payment_method == self.CREDIT and
            not self.paid and
            self.due_date and
            self.due_date < timezone.now().date()
        )

    @property
    def subtotal(self):
        """Calculate subtotal before discounts and taxes"""
        return sum(item.total_price for item in self.items.all())

    @property
    def discount_amount(self):
        """Calculate discount amount"""
        return self.subtotal * (self.discount_percentage / 100)

    @property
    def tax_amount(self):
        """Calculate tax amount"""
        return (self.subtotal - self.discount_amount) * (self.tax_percentage / 100)

    def convert_to_sale(self, payment_method, reference_number=None, amount_tendered=0, change_amount=0):
        """Convert a proforma invoice to a regular sale"""
        with transaction.atomic():
            if not self.is_proforma:
                raise ValidationError(_("Only proforma invoices can be converted to sales"))

            self.is_proforma = False
            self.paid = True
            self.status = self.STATUS_COMPLETED
            self.payment_method = payment_method
            self.reference_number = reference_number or ""
            self.amount_tendered = amount_tendered
            self.change_amount = change_amount

            # Generate a new invoice number for the converted sale
            last_id = Sale.objects.filter(is_proforma=False).aggregate(max_id=models.Max('id'))['max_id'] or 0
            self.invoice_number = f"INV-{last_id + 1:06d}"
            self.save()

            # Update inventory for all items in the sale
            for item in self.items.all():
                item.product.quantity_in_stock -= item.quantity
                item.product.save()

        return True

    def get_absolute_url(self):
        """Return the URL to access a detail record for this sale"""
        return reverse('inventory:sale-detail', kwargs={'pk': self.pk})


class SaleItem(models.Model):
    """
    Sales line items representing products sold to customers.
    """
    sale = models.ForeignKey(
        Sale,
        related_name='items',
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Cost price at time of sale")
    )
   
    class Meta:
        verbose_name = _("Sale Item")
        verbose_name_plural = _("Sale Items")
        unique_together = ['sale', 'product']
   
    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
   
    @property
    def total_price(self):
        """Calculate total price for this line item"""
        return self.quantity * (self.unit_price - self.discount)
   
    @property
    def profit(self):
        """Calculate profit for this line item"""
        return self.total_price - (self.quantity * self.cost_price)
   
    def clean(self):
        if self.discount >= self.unit_price:
            raise ValidationError(_("Discount cannot be greater than or equal to unit price"))
        
        # Only check stock for non-proforma sales
        if self.product and not self.sale.is_proforma and self.quantity > self.product.quantity_in_stock:
            raise ValidationError(_("Not enough stock available"))
   
    def save(self, *args, **kwargs):
        # Set cost price from product if not provided
        if not self.cost_price and self.product:
            self.cost_price = self.product.cost_price
           
        super().save(*args, **kwargs)
       
        # Update parent sale total
        self.sale.save()

class StockAdjustment(TimestampModel):
    """
    Stock adjustment model for tracking inventory changes outside of
    normal sales and purchase processes.
    """
    INCREASE = 'increase'
    DECREASE = 'decrease'
    
    ADJUSTMENT_TYPE_CHOICES = [
        (INCREASE, _('Increase')),
        (DECREASE, _('Decrease')),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_adjustments'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    adjustment_type = models.CharField(
        max_length=10,
        choices=ADJUSTMENT_TYPE_CHOICES
    )
    reason = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    adjusted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='stock_adjustments'
    )
    notes = models.TextField(blank=True)
    reference_number = models.CharField(max_length=50, unique=True, blank=True, default='')

    class Meta:
        ordering = ['-date']
        verbose_name = _("Stock Adjustment")
        verbose_name_plural = _("Stock Adjustments")
    
    def __str__(self):
        return f"{self.get_adjustment_type_display()} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Create the adjustment first
        is_new = not self.pk  # Add this line to define is_new
        
        if not self.reference_number:
            today = timezone.now()
            date_str = today.strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            self.reference_number = f'ADJ-{date_str}-{random_str}'
        
        super().save(*args, **kwargs)
        
        # Then update the product quantity if this is a new adjustment
        if is_new:
            product = self.product
            if self.adjustment_type == self.INCREASE:
                product.quantity_in_stock += self.quantity
                if not product.last_restocked:
                    product.last_restocked = self.date
            else:
                # Ensure we don't go below zero
                new_quantity = max(0, product.quantity_in_stock - self.quantity)
                product.quantity_in_stock = new_quantity
            
            product.save()
class StockMovement(models.Model):
    """Model for tracking stock movements."""
    MOVEMENT_TYPES = (
        ('restock', 'Restock'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('stock_add', 'Stock Addition'),
        ('stock_remove', 'Stock Removal'),
        ('stock_set', 'Stock Set'),
        ('adjustment', 'Adjustment'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    quantity = models.IntegerField()
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reference_id = models.IntegerField(null=True, blank=True, help_text="ID of the related transaction (sale, purchase, etc.)")

    class Meta:
        ordering = ['-created_at']
   
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"

class ReservedStock(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reserved_stock')
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='reserved_items')
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'sale')
        verbose_name = _('Reserved Stock')
        verbose_name_plural = _('Reserved Stock')

    def __str__(self):
        return f"{self.quantity} of {self.product.name} reserved for {self.sale.invoice_number}"

class InventoryCount(TimestampModel):
    """
    Inventory count model for tracking physical inventory counts.
    """
    count_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', _('Draft')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
            ('cancelled', _('Cancelled')),
        ],
        default='draft'
    )
    counted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inventory_counts'
    )
    
    class Meta:
        ordering = ['-count_date']
        verbose_name = _("Inventory Count")
        verbose_name_plural = _("Inventory Counts")
    
    def __str__(self):
        return f"Count #{self.id} - {self.count_date}"
    
    @property
    def discrepancy_count(self):
        """Count items with discrepancies"""
        return self.items.exclude(
            system_quantity=models.F('counted_quantity')
        ).count()


class InventoryCountItem(models.Model):
    """
    Individual items in an inventory count.
    """
    inventory_count = models.ForeignKey(
        InventoryCount,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='count_items'
    )
    system_quantity = models.PositiveIntegerField()
    counted_quantity = models.PositiveIntegerField()
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ['inventory_count', 'product']
        verbose_name = _("Inventory Count Item")
        verbose_name_plural = _("Inventory Count Items")
    
    def __str__(self):
        return f"{self.product.name} - System: {self.system_quantity}, Counted: {self.counted_quantity}"

    @property
    def has_discrepancy(self):
        """Check if there's a discrepancy between system and counted quantities"""
        return self.system_quantity != self.counted_quantity
    
    @property
    def discrepancy(self):
        """Calculate the discrepancy amount"""
        return self.counted_quantity - self.system_quantity


class PaymentReceived(TimestampModel):
    """
    Payment received model for tracking customer payments.
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(
        max_length=50,
        choices=Sale.PAYMENT_METHOD_CHOICES
    )
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_payments'
    )
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = _("Payment Received")
        verbose_name_plural = _("Payments Received")
    
    def __str__(self):
        return f"Payment of {self.amount} for {self.sale.invoice_number}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Check if sale is fully paid
        sale = self.sale
        total_paid = sum(payment.amount for payment in sale.payments.all())
        
        if total_paid >= sale.total_amount:
            sale.paid = True
            sale.save()


class Warranty(TimestampModel):
    """
    Warranty model for tracking product warranties.
    """
    sale_item = models.OneToOneField(
        SaleItem,
        on_delete=models.CASCADE,
        related_name='warranty'
    )
    warranty_start = models.DateField(default=timezone.now)
    warranty_end = models.DateField()
    serial_number = models.CharField(max_length=100, blank=True)
    terms = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-warranty_end']
        verbose_name = _("Warranty")
        verbose_name_plural = _("Warranties")
    
    def __str__(self):
        return f"Warranty for {self.sale_item.product.name} - {self.serial_number}"
    
    @property
    def is_valid(self):
        """Check if warranty is still valid"""
        return self.warranty_end >= timezone.now().date()
    
    @property
    def days_remaining(self):
        """Calculate days remaining in warranty"""
        if self.is_valid:
            delta = self.warranty_end - timezone.now().date()
            return delta.days
        return 0


class WarrantyClaim(TimestampModel):
    """
    Warranty claim model for tracking customer warranty claims.
    """
    warranty = models.ForeignKey(
        Warranty,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claim_date = models.DateField(default=timezone.now)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('resolved', _('Resolved')),
        ],
        default='pending'
    )
    resolution = models.TextField(blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-claim_date']
        verbose_name = _("Warranty Claim")
        verbose_name_plural = _("Warranty Claims")
    
    def __str__(self):
        return f"Claim for {self.warranty.sale_item.product.name} - {self.get_status_display()}"

class SystemSettings(models.Model):
    """
    System-wide settings for the inventory application.
    """
    company_name = models.CharField(max_length=200)
    company_address = models.TextField()
    company_phone = models.CharField(max_length=20)
    company_email = models.EmailField()
    company_website = models.URLField(blank=True)
    company_logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    currency_symbol = models.CharField(max_length=5, default='$')
    low_stock_threshold = models.PositiveIntegerField(default=5)
    enable_email_notifications = models.BooleanField(default=True)
    default_payment_terms = models.CharField(max_length=100, default='Due on receipt')
    
    class Meta:
        verbose_name = _("System Settings")
        verbose_name_plural = _("System Settings")
    
    def __str__(self):
        return self.company_name
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if SystemSettings.objects.exists() and not self.pk:
            raise ValidationError(_("Only one system settings instance can exist"))
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create system settings"""
        settings, created = cls.objects.get_or_create(
            defaults={
                'company_name': 'Solar Inventory System',
                'company_address': 'Default Address',
                'company_phone': '123-456-7890',
                'company_email': 'info@example.com',
            }
        )
        return settings

class Notification(TimestampModel):
    """
    Notification model for system notifications.
    """
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    read = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    link = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
    
    def __str__(self):
        return self.title
    
    @classmethod
    def create_low_stock_notification(cls, product, user=None):
        """Create notification for low stock products"""
        title = _("Low Stock Alert")
        message = _(f"Product '{product.name}' is low on stock. Current quantity: {product.quantity_in_stock}")
        
        # If no specific user, notify all inventory managers
        if not user:
            for manager in User.objects.filter(is_inventory_manager=True):
                cls.objects.create(
                    user=manager,
                    title=title,
                    message=message,
                    priority='high',
                    link=f"/inventory/products/{product.id}/"
                )
        else:
            cls.objects.create(
                user=user,
                title=title,
                message=message,
                priority='high',
                link=f"/inventory/products/{product.id}/"
            )

class Location(models.Model):
    """Model representing a physical storage location for inventory items"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'

class HeldSale(models.Model):
    """
    Model for sales that are held/saved for later processing
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who created this held sale")
    )
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Customer"),
        help_text=_("Customer for this sale")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes about this held sale")
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Amount"),
        help_text=_("Total amount of this sale")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Date and time when this sale was held")
    )
    
    class Meta:
        verbose_name = _("Held Sale")
        verbose_name_plural = _("Held Sales")
        ordering = ['-created_at']
    
    def __str__(self):
        if self.customer:
            return f"Held Sale #{self.id} - {self.customer.name}"
        return f"Held Sale #{self.id}"

class HeldSaleItem(models.Model):
    """
    Model for items in a held sale
    """
    held_sale = models.ForeignKey(
        HeldSale,
        on_delete=models.CASCADE,
        verbose_name=_("Held Sale"),
        help_text=_("The held sale this item belongs to")
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        verbose_name=_("Product"),
        help_text=_("Product for this sale item")
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Quantity"),
        help_text=_("Quantity of product")
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Unit Price"),
        help_text=_("Price per unit")
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Discount Amount"),
        help_text=_("Discount amount for this item")
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Total Price"),
        help_text=_("Total price for this item")
    )
    
    class Meta:
        verbose_name = _("Held Sale Item")
        verbose_name_plural = _("Held Sale Items")
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Brand, Supplier, ProductCategory, Product, ProductImage, 
    ProductSpecification, Customer, PurchaseOrder, PurchaseOrderItem, 
    Sale, SaleItem, StockAdjustment, StockMovement, ReservedStock, 
    InventoryCount, InventoryCountItem, PaymentReceived, Warranty, 
    WarrantyClaim, SystemSettings, Notification, Location, HeldSale, 
    HeldSaleItem
)


# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role_display', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_sales_person', 'is_inventory_manager', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        (_('Additional Information'), {'fields': ('phone', 'is_sales_person', 'is_inventory_manager', 'profile_image', 'department', 'employee_id')}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'employee_id')


# Brand Admin
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active', 'product_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'logo', 'is_active')
        }),
        (_('Contact Information'), {
            'fields': ('website', 'contact_email', 'contact_phone')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Supplier Admin
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active', 'product_count', 'total_orders')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'product_count', 'total_orders', 'pending_orders')
    fieldsets = (
        (None, {
            'fields': ('name', 'contact_person', 'is_active')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone', 'address', 'website')
        }),
        (_('Business Information'), {
            'fields': ('tax_id', 'payment_terms', 'lead_time_days')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Statistics'), {
            'fields': ('product_count', 'total_orders', 'pending_orders'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Product Category Admin
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'product_count')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'parent', 'is_active', 'icon')
        }),
        (_('Statistics'), {
            'fields': ('product_count',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Product Image Inline
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


# Product Specification Inline
class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1


# Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'brand', 'unit_price', 'quantity_in_stock', 'active', 'stock_status')
    list_filter = ('active', 'category', 'brand', 'is_featured')
    search_fields = ('name', 'sku', 'description', 'barcode')
    readonly_fields = ('created_at', 'updated_at', 'profit_margin', 'stock_value', 'needs_restock')
    fieldsets = (
        (None, {
            'fields': ('name', 'sku', 'description', 'active', 'is_featured')
        }),
        (_('Categorization'), {
            'fields': ('category', 'brand', 'tags')
        }),
        (_('Pricing'), {
            'fields': ('unit_price', 'cost_price', 'profit_margin')
        }),
        (_('Inventory'), {
            'fields': ('quantity_in_stock', 'minimum_stock_level', 'stock_value', 'needs_restock', 'last_restocked')
        }),
        (_('Supplier Information'), {
            'fields': ('supplier',)
        }),
        (_('Product Details'), {
            'fields': ('image', 'barcode', 'weight', 'dimensions', 'warranty_period')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ProductImageInline, ProductSpecificationInline]
    
    def stock_status(self, obj):
        if obj.quantity_in_stock <= 0:
            return format_html('<span style="color: red; font-weight: bold;">Out of Stock</span>')
        elif obj.needs_restock:
            return format_html('<span style="color: orange; font-weight: bold;">Low Stock</span>')
        else:
            return format_html('<span style="color: green;">In Stock</span>')
    stock_status.short_description = _('Stock Status')


# Customer Admin
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'is_active', 'total_purchases', 'last_purchase_date')
    list_filter = ('is_active',)
    search_fields = ('name', 'email', 'phone', 'company_name')
    readonly_fields = ('created_at', 'updated_at', 'total_purchases', 'last_purchase_date')
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'phone', 'is_active')
        }),
        (_('Business Information'), {
            'fields': ('company_name', 'tax_id', 'credit_limit')
        }),
        (_('Additional Information'), {
            'fields': ('address', 'date_of_birth', 'notes')
        }),
        (_('User Account'), {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('total_purchases', 'last_purchase_date'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Purchase Order Item Inline
class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    readonly_fields = ('total_price', 'received_status')


# Purchase Order Admin
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'order_date', 'expected_delivery_date', 'status', 'total_amount', 'is_overdue')
    list_filter = ('status', 'order_date')
    search_fields = ('order_number', 'supplier__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'total_cost', 'is_overdue', 'days_until_delivery')
    fieldsets = (
        (None, {
            'fields': ('order_number', 'supplier', 'status')
        }),
        (_('Dates'), {
            'fields': ('order_date', 'expected_delivery_date', 'received_date')
        }),
        (_('Financial'), {
            'fields': ('shipping_cost', 'tax_amount', 'total_amount', 'total_cost')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'is_overdue', 'days_until_delivery')
        }),
        (_('Users'), {
            'fields': ('created_by', 'received_by')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [PurchaseOrderItemInline]


# Sale Item Inline
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ('total_price', 'profit')


# Payment Received Inline
class PaymentReceivedInline(admin.TabularInline):
    model = PaymentReceived
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


# Sale Admin
class SaleAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'sale_date', 'total_amount', 'payment_method', 'status', 'paid')
    list_filter = ('status', 'paid', 'payment_method', 'sale_date')
    search_fields = ('invoice_number', 'customer__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'subtotal', 'discount_amount', 'tax_amount', 'is_overdue')
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'customer', 'sales_person', 'status')
        }),
        (_('Sale Details'), {
            'fields': ('sale_date', 'payment_method', 'paid', 'is_proforma')
        }),
        (_('Financial'), {
            'fields': ('subtotal', 'discount_percentage', 'discount_amount', 'tax_percentage', 'tax_amount', 'shipping_cost', 'total_amount')
        }),
        (_('Payment Information'), {
            'fields': ('reference_number', 'amount_tendered', 'change_amount', 'due_date', 'is_overdue')
        }),
        (_('Additional Information'), {
            'fields': ('notes',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [SaleItemInline, PaymentReceivedInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer', 'sales_person')


# Stock Adjustment Admin
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'product', 'quantity', 'adjustment_type', 'date', 'adjusted_by')
    list_filter = ('adjustment_type', 'date')
    search_fields = ('product__name', 'product__sku', 'reason', 'reference_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('reference_number', 'product', 'quantity', 'adjustment_type')
        }),
        (_('Details'), {
            'fields': ('reason', 'date', 'notes')
        }),
        (_('User'), {
            'fields': ('adjusted_by',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Stock Movement Admin
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'movement_type', 'created_at', 'created_by')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('product__name', 'product__sku', 'notes')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('product', 'quantity', 'movement_type')
        }),
        (_('Details'), {
            'fields': ('notes', 'reference_id')
        }),
        (_('User'), {
            'fields': ('created_by',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Reserved Stock Admin
class ReservedStockAdmin(admin.ModelAdmin):
    list_display = ('product', 'sale', 'quantity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'product__sku', 'sale__invoice_number')
    readonly_fields = ('created_at', 'updated_at')


# Inventory Count Item Inline
class InventoryCountItemInline(admin.TabularInline):
    model = InventoryCountItem
    extra = 1
    readonly_fields = ('has_discrepancy', 'discrepancy')


# Inventory Count Admin
class InventoryCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'count_date', 'status', 'counted_by', 'discrepancy_count')
    list_filter = ('status', 'count_date')
    search_fields = ('notes',)
    readonly_fields = ('created_at', 'updated_at', 'discrepancy_count')
    fieldsets = (
        (None, {
            'fields': ('count_date', 'status', 'counted_by')
        }),
        (_('Details'), {
            'fields': ('notes', 'discrepancy_count')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [InventoryCountItemInline]


# Warranty Admin
class WarrantyAdmin(admin.ModelAdmin):
    list_display = ('sale_item', 'serial_number', 'warranty_start', 'warranty_end', 'is_valid', 'days_remaining')
    list_filter = ('warranty_start', 'warranty_end')
    search_fields = ('serial_number', 'sale_item__product__name')
    readonly_fields = ('created_at', 'updated_at', 'is_valid', 'days_remaining')
    fieldsets = (
        (None, {
            'fields': ('sale_item', 'serial_number')
        }),
        (_('Warranty Period'), {
            'fields': ('warranty_start', 'warranty_end', 'is_valid', 'days_remaining')
        }),
        (_('Terms'), {
            'fields': ('terms',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Warranty Claim Admin
class WarrantyClaimAdmin(admin.ModelAdmin):
    list_display = ('warranty', 'claim_date', 'status', 'resolved_date')
    list_filter = ('status', 'claim_date', 'resolved_date')
    search_fields = ('warranty__serial_number', 'description', 'resolution')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('warranty', 'claim_date', 'status')
        }),
        (_('Claim Details'), {
            'fields': ('description',)
        }),
        (_('Resolution'), {
            'fields': ('resolution', 'resolved_date')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# System Settings Admin
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company_email', 'tax_rate', 'currency_symbol')
    fieldsets = (
        (_('Company Information'), {
            'fields': ('company_name', 'company_address', 'company_phone', 'company_email', 'company_website', 'company_logo')
        }),
        (_('Financial Settings'), {
            'fields': ('tax_rate', 'currency_symbol', 'default_payment_terms')
        }),
        (_('System Settings'), {
            'fields': ('low_stock_threshold', 'enable_email_notifications')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow adding if no settings exist
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting the settings
        return False


# Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'read', 'created_at')
    list_filter = ('priority', 'read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message', 'priority', 'read')
        }),
        (_('Link'), {
            'fields': ('link',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Location Admin
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        (_('Address'), {
            'fields': ('address',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Held Sale Item Inline
class HeldSaleItemInline(admin.TabularInline):
    model = HeldSaleItem
    extra = 1
    readonly_fields = ('total_price',)


# Held Sale Admin
class HeldSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'user', 'total_amount', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('customer__name', 'notes')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('user', 'customer', 'total_amount')
        }),
        (_('Details'), {
            'fields': ('notes',)
        }),
        (_('Metadata'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    inlines = [HeldSaleItemInline]


# Register all models with the admin site
admin.site.register(User, CustomUserAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(ProductSpecification)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(PurchaseOrderItem)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem)
admin.site.register(StockAdjustment, StockAdjustmentAdmin)
admin.site.register(StockMovement, StockMovementAdmin)
admin.site.register(ReservedStock, ReservedStockAdmin)
admin.site.register(InventoryCount, InventoryCountAdmin)
admin.site.register(InventoryCountItem)
admin.site.register(PaymentReceived)
admin.site.register(Warranty, WarrantyAdmin)
admin.site.register(WarrantyClaim, WarrantyClaimAdmin)
admin.site.register(SystemSettings, SystemSettingsAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(HeldSale, HeldSaleAdmin)
admin.site.register(HeldSaleItem)


# Customize admin site
admin.site.site_header = _("Solar Inventory Administration")
admin.site.site_title = _("Solar Inventory Admin")
admin.site.index_title = _("Dashboard")

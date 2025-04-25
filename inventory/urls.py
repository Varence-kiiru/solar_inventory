from django.urls import path, include
from . import views
from .views import (DashboardView, BrandListView, BrandCreateView, BrandDetailView, BrandUpdateView, BrandDeleteView,
                    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView,
                    ProductExportView, ProductExportTemplateView, ProductImportView, ProductImportResultView,
                    ProductBulkUpdateView, ProductBulkDeleteView, CategoryListView, CategoryCreateView, CategoryUpdateView,
                    CategoryDeleteView, CustomerListView, CustomerDetailView,CustomerCreateView, CustomerUpdateView,
                    SupplierListView, PurchaseOrderListView,PurchaseOrderCreateView, SaleListView, POSView, SaleDetailView,
                    InventoryReportView)

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', DashboardView.as_view(), name='dashboard'),

    # Brand URLs
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('brands/create/', BrandCreateView.as_view(), name='brand-create'),
    path('brands/<int:pk>/', BrandDetailView.as_view(), name='brand-detail'),
    path('brands/<int:pk>/update/', BrandUpdateView.as_view(), name='brand-update'),
    path('brands/<int:pk>/delete/', BrandDeleteView.as_view(), name='brand-delete'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('products/export/', ProductExportView.as_view(), name='product-export'),
    path('products/export-template/', ProductExportTemplateView.as_view(), name='product-export-template'),
    path('products/import/', ProductImportView.as_view(), name='product-import'),
    path('products/import-result/', ProductImportResultView.as_view(), name='product-import-result'),
    path('products/bulk-update/', ProductBulkUpdateView.as_view(), name='product-bulk-update'),
    path('products/bulk-delete/', ProductBulkDeleteView.as_view(), name='product-bulk-delete'),
    path('products/categories/', CategoryListView.as_view(), name='category-list'),
    path('products/categories/create/', CategoryCreateView.as_view(), name='category-create'),
    path('products/categories/<int:pk>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('products/categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
    path('products/<int:pk>/restock/', views.ProductRestockView.as_view(), name='product-restock'),
    path('products/<int:pk>/adjust-stock/', views.ProductAdjustStockView.as_view(), name='product-adjust-stock'),
    path('products/search/barcode/', views.product_search_barcode, name='product-search-barcode'),
    path('proforma/list/', views.proforma_list, name='proforma-list'),


    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),

    # Sales
    path('pos/', POSView.as_view(), name='pos'),
    path('sales/', SaleListView.as_view(), name='sale-list'),
    path('sales/create/', views.SaleCreateView.as_view(), name='sale-create'),
    path('sales/<int:pk>/', SaleDetailView.as_view(), name='sale-detail'),
    path('sales/email-invoice/', views.sale_email_invoice, name='sale-email-invoice'),
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', views.InvoiceView.as_view(), name='invoice-view'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice-pdf'),
    path('invoices/<int:pk>/download/', views.invoice_pdf_download, name='invoice-pdf-download'),
    path('invoice/<int:sale_id>/content/', views.invoice_content, name='invoice-partial'),
    path('inventory/api/sales/hold/', views.hold_sale, name='hold-sale'),
    path('inventory/api/sales/held/', views.get_held_sales, name='get-held-sales'),
    path('inventory/api/sales/held/<int:sale_id>/', views.get_held_sale, name='get-held-sale'),
    path('inventory/api/sales/held/<int:sale_id>/delete/', views.delete_held_sale, name='delete-held-sale'),
    path('proforma/convert/', views.proforma_convert, name='proforma-convert'),
    path('sales/<int:pk>/mark-paid/', views.mark_sale_paid, name='mark-sale-paid'),


    # Customers
    path('customers/', CustomerListView.as_view(), name='customer-list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer-create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),
    path('customers/<int:pk>/update/', CustomerUpdateView.as_view(), name='customer-update'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer-delete'),
    path('customers/create-ajax/', views.customer_create_ajax, name='customer-create-ajax'),

    # Suppliers
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    path('suppliers/<int:pk>/update/', views.SupplierUpdateView.as_view(), name='supplier-update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier-delete'),

    # Purchase Orders
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='purchase-order-list'),
    path('purchase-orders/create/', views.PurchaseOrderCreateView.as_view(), name='purchase-order-create'),
    path('purchase-orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase-order-detail'),
    path('purchase-orders/<int:pk>/update/', views.PurchaseOrderUpdateView.as_view(), name='purchase-order-update'),
    path('purchase-orders/<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='purchase-order-delete'),
    path('purchase-orders/<int:pk>/receive/', views.PurchaseOrderReceiveView.as_view(), name='purchase-order-receive'),

    # Inventory Management
    path('stock-adjustments/', views.StockAdjustmentListView.as_view(), name='stock-adjustment-list'),
    path('stock-adjustments/create/', views.StockAdjustmentCreateView.as_view(), name='stock-adjustment-create'),
    path('stock-adjustments/<int:pk>/', views.StockAdjustmentDetailView.as_view(), name='stock-adjustment-detail'),
    path('stock-adjustments/<int:pk>/update/', views.StockAdjustmentUpdateView.as_view(), name='stock-adjustment-update'),
    path('stock-adjustments/<int:pk>/delete/', views.StockAdjustmentDeleteView.as_view(), name='stock-adjustment-delete'),
    path('stock-count/', views.StockCountView.as_view(), name='stock-count'),

    # Reports
    path('reports/sales/', views.SalesReportView.as_view(), name='sales-report'),
    path('reports/inventory/', InventoryReportView.as_view(), name='inventory-report'),
    path('reports/customers/', views.CustomerReportView.as_view(), name='customer-report'),
    path('reports/low-stock/', views.LowStockReportView.as_view(), name='low-stock-report'),
    path('reports/low-stock/export-excel/', views.LowStockExportExcelView.as_view(), name='low-stock-export-excel'),
    path('reports/low-stock/export-pdf/', views.LowStockExportPDFView.as_view(), name='low-stock-export-pdf'),

    # User Management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('users/', views.UserManagementView.as_view(), name='user-management'),

  
]

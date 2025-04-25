# inventory/context_processors.py
from .models import Product
from .models import SystemSettings

def settings_processor(request):
    """
    Context processor that adds system settings to all templates
    """
    try:
        settings = SystemSettings.objects.first()
        if not settings:
            settings = SystemSettings.objects.create(
                company_name='Inventory System',
                company_address='Default Address',
                company_phone='123-456-7890',
                company_email='info@example.com'
            )
    except:
        # If database isn't set up yet or there's an error
        settings = None
    
    return {'settings': settings}

def inventory_alerts(request):
    return {
        'low_stock_products': Product.get_low_stock_products()
    }
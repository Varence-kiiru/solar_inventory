# inventory/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Product

@receiver(post_save, sender=Product)
def check_stock_levels(sender, instance, **kwargs):
    if instance.needs_restock:
        subject = f"Low Stock Alert: {instance.name}"
        message = render_to_string('inventory/low_stock_email.txt', {
            'product': instance,
        })
        send_mail(
            subject,
            message,
            'inventory@yourcompany.com',
            ['manager@yourcompany.com'],
            fail_silently=True,
        )
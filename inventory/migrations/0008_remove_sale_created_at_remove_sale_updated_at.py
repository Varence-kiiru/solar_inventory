# Generated by Django 5.1.7 on 2025-03-30 15:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_sale_amount_tendered_sale_change_amount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sale',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='sale',
            name='updated_at',
        ),
    ]

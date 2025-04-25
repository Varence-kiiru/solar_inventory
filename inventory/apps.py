from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # Import signals and other startup code
        from . import context_processors
        from . import signals
        from . import models
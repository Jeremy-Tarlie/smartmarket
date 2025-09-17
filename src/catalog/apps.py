from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
    
    def ready(self):
        """Importe les signaux lors du démarrage de l'application."""
        import catalog.signals
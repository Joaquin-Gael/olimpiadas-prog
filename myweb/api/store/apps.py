from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api.store'
    verbose_name = 'Store'

    def ready(self):
        # Importa aquí para que Django registre los receivers
        from . import signals   # noqa

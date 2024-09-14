from django.apps import AppConfig


class FeedsConfig(AppConfig):
    name = 'feeds'

    def ready(self):
        import feeds.signals  # Import signals to ensure they're loaded
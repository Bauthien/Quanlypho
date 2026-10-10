from django.apps import AppConfig


class PhoAppConfig(AppConfig):
    name = 'pho_app'

    def ready(self):
        import pho_app.signals

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class LiveResultsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'live_results'
    verbose_name = _("Wyniki na Żywo")

    def ready(self):
        """
        Metoda wywoływana, gdy aplikacja jest gotowa.
        Idealne miejsce do importowania sygnałów.
        """
        from . import signals
        print("Live Results Signals Imported.")
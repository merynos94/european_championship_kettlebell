from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class LiveResultsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # Upewnij się, że 'name' odpowiada ścieżce do Twojej aplikacji w projekcie Django
    # Zazwyczaj jest to po prostu nazwa katalogu aplikacji.
    name = 'live_results'
    verbose_name = _("Wyniki na Żywo") # Opcjonalna, bardziej przyjazna nazwa

    def ready(self):
        """
        Metoda wywoływana, gdy aplikacja jest gotowa.
        Idealne miejsce do importowania sygnałów.
        """
        from . import signals
        print("Live Results Signals Imported.")
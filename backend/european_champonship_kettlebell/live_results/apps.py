from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LiveResultsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "live_results"
    verbose_name = _("Wyniki na Żywo")

    def ready(self):
        import live_results.signals

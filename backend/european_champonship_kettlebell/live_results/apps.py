"""European Kettlebell Championships Apps module"""

from django.apps import AppConfig


class LiveResultsConfig(AppConfig):
    """Configuration for the Live Results app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "live_results"

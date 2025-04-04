"""Model definition for SportClub."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class SportClub(models.Model):
    """Represents a sports club."""

    name = models.CharField(_("Nazwa Klubu"), max_length=100, unique=True)  # Dodano unique=True?

    class Meta:
        verbose_name = _("Klub")
        verbose_name_plural = _("Kluby")
        ordering = ["name"]  # Dobra praktyka - domyślne sortowanie

    def __str__(self) -> str:
        return self.name

"""Model definition for Category."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import AVAILABLE_DISCIPLINES, DISCIPLINE_NAMES


class Category(models.Model):
    """Represents a competition category with specific disciplines."""

    name = models.CharField(_("Nazwa Kategorii"), max_length=100, unique=True)  # Dodano unique=True?
    disciplines = models.JSONField(_("Disciplines"), default=list)

    class Meta:
        verbose_name = _("Kategorie")
        verbose_name_plural = _("Kategorie")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def set_disciplines(self, disciplines: list[str]) -> None:
        """Sets the list of disciplines, ensuring they are valid."""
        valid_disciplines = [d[0] for d in AVAILABLE_DISCIPLINES]
        self.disciplines = sorted([d for d in disciplines if d in valid_disciplines])  # Sortowanie dla spójności

    def get_disciplines(self) -> list[str]:
        """Returns the list of disciplines for this category."""
        return self.disciplines

    def get_disciplines_display(self) -> str:
        """Returns a comma-separated string of human-readable discipline names."""
        return ", ".join(DISCIPLINE_NAMES.get(d, d) for d in self.disciplines)

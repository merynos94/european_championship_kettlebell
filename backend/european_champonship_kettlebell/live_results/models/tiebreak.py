# Plik: np. live_results/models/tiebreak.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from .player import Player

from .category import Category

class PlayerCategoryTiebreak(models.Model):
    """Stores information about applying a tiebreak for a specific player in a specific category."""
    player = models.ForeignKey(
        "live_results.Player", # Użyj poprawnej ścieżki do modelu Player
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="tiebreaks_applied", # Można zmienić related_name
    )
    category = models.ForeignKey(
        "live_results.Category", # Użyj poprawnej ścieżki do modelu Category
        on_delete=models.CASCADE,
        verbose_name=_("Kategoria"),
        related_name="tiebreaks_applied", # Można zmienić related_name
    )
    # Samo istnienie rekordu oznacza zastosowanie tiebreaka.
    # Można by dodać pole boolean 'apply_tiebreak = BooleanField(default=True)',
    # ale dla prostoty - istnienie rekordu = zastosuj.

    class Meta:
        verbose_name = _("Zastosowany Tiebreak (Zawodnik-Kategoria)")
        verbose_name_plural = _("Zastosowane Tiebreaki (Zawodnik-Kategoria)")
        # Unikalność dla pary zawodnik-kategoria
        unique_together = ('player', 'category')
        ordering = ["player__surname", "player__name", "category__name"]

    def __str__(self):
        player_name = str(self.player) if hasattr(self, "player") and self.player else "?"
        cat_name = str(self.category) if hasattr(self, "category") and self.category else "?"
        return f"Tiebreak dla: {player_name} w kat. {cat_name}"
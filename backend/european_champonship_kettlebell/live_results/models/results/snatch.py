"""Model definition for SnatchResult."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class SnatchResult(models.Model):
    """Stores the result for the Snatch discipline."""

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="snatch_result",  # Ważny related_name
    )
    result = models.FloatField(_("Wynik Snatch (Waga*Powt.)"), null=True, blank=True)
    position = models.IntegerField(_("Pozycja w konkurencji"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Snatch")
        verbose_name_plural = _("Wyniki Snatch")
        # Sortowanie wg wyniku malejąco (lepszy wynik = wyższy)
        ordering = ["player__categories", "-result"]

    def __str__(self) -> str:
        score = f"{self.result:.1f}" if self.result is not None else _("N/A")
        player_name = getattr(self.player, "full_name", "N/A")
        return f"{player_name} - Snatch: {score}"

"""Model definition for TGUResult."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TGUResult(models.Model):
    """Stores the results for the Turkish Get-Up discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player", on_delete=models.CASCADE, verbose_name=_("Player"), related_name="tgu_result"
    )
    result_1 = models.FloatField(_("Próba I"), default=0.0, null=True, blank=True)
    result_2 = models.FloatField(_("Próba II"), default=0.0, null=True, blank=True)
    result_3 = models.FloatField(_("Próba III"), default=0.0, null=True, blank=True)
    position = models.IntegerField(_("Miejsce w kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Turkish Get-Up")
        verbose_name_plural = _("Wyniki Turkish Get-Up")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
        return f"{self.player} - TGU Attempts: {self.result_1 or 0}/{self.result_2 or 0}/{self.result_3 or 0}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        # Zwraca 0.0 jeśli wszystkie próby są None lub 0.0
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        # Bezpieczne pobranie gracza i jego wagi
        player = getattr(self, "player", None)
        if not player:
            return None
        player_weight = getattr(player, "weight", None)

        # Obliczenie procentu
        max_res = self.max_result
        if player_weight and player_weight > 0 and max_res > 0:
            return round((max_res / player_weight) * 100, 2)
        return None

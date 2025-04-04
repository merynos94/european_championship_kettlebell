"""Model definition for OneKettlebellPressResult."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass


class OneKettlebellPressResult(models.Model):
    """Stores the results for the One Kettlebell Press discipline attempts (1RM)."""

    player = models.OneToOneField(
        "Player", on_delete=models.CASCADE, verbose_name=_("Player"), related_name="one_kettlebell_press_result"
    )
    result_1 = models.FloatField(_("Próba I Kettlebell Press"), default=0.0)
    result_2 = models.FloatField(_("Próba II Kettlebell Press"), default=0.0)
    result_3 = models.FloatField(_("Próba III Kettlebell Press"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Kettlebell Press")
        verbose_name_plural = _("Wyniki Kettlebell Press")
        ordering = ["player__categories", "-position"]  # Sortowanie wg pozycji

    def __str__(self) -> str:
        return f"{self.player} - One KB Press Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        if self.player.weight and self.player.weight > 0:
            return round((self.max_result / self.player.weight) * 100, 2)
        return None

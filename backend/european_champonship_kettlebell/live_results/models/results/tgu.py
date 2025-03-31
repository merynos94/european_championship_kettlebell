# -*- coding: utf-8 -*-
"""Model definition for TGUResult."""
from typing import Optional, TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player

class TGUResult(models.Model):
    """Stores the results for the Turkish Get-Up discipline attempts."""
    player = models.OneToOneField['Player'](
        'Player',
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="tgu_result"
    )
    result_1 = models.FloatField(_("Attempt 1 Weight"), default=0.0)
    result_2 = models.FloatField(_("Attempt 2 Weight"), default=0.0)
    result_3 = models.FloatField(_("Attempt 3 Weight"), default=0.0)
    position = models.IntegerField(_("Position in Category"), null=True, blank=True)

    class Meta:
        verbose_name = _("TGU Result")
        verbose_name_plural = _("TGU Results")
        ordering = ['player__categories', '-position'] # Sortowanie wg pozycji

    def __str__(self) -> str:
        return f"{self.player} - TGU Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> Optional[float]:
        """Calculates the max result as a percentage of player's body weight."""
        if self.player.weight and self.player.weight > 0:
            return round((self.max_result / self.player.weight) * 100, 2)
        return None
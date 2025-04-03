# -*- coding: utf-8 -*-
"""Model definition for OneKettlebellPressResult."""
from typing import Optional, TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę jeśli Player jest gdzie indziej

class OneKettlebellPressResult(models.Model):
    """Stores the results for the One Kettlebell Press discipline attempts (1RM)."""
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="one_kettlebell_press_result"
    )
    result_1 = models.FloatField(_("Próba I Kettlebell Press"), default=0.0)
    result_2 = models.FloatField(_("Próba II Kettlebell Press"), default=0.0)
    result_3 = models.FloatField(_("Próba III Kettlebell Press"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Kettlebell Press")
        verbose_name_plural = _("Wyniki Kettlebell Press")
        ordering = ['player__categories', '-position'] # Sortowanie wg pozycji

    def __str__(self) -> str:
        return f"{self.player} - One KB Press Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

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


from typing import TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _
# Zaimportuj model OneKettlebellPressResult


if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę

class BestOneKettlebellPressResult(models.Model):
    """Stores the best One Kettlebell Press result per player."""
    player = models.OneToOneField['Player'](
        'Player',
        on_delete=models.CASCADE,
        related_name='best_one_kettlebell_press_result' # Ważne: unikalna related_name
    )
    best_result = models.FloatField(_("Best One KB Press Result"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Kettlebell Press")
        verbose_name_plural = _("Najlepsze Wyniki Kettlebell Press")

    def update_best_result(self) -> bool:
        """Updates the best result based on the associated OneKettlebellPressResult's max_result."""
        try:
            press_result = self.player.one_kettlebell_press_result # Użyj related_name z OneKettlebellPressResult
            new_best_result = press_result.max_result

            if self.best_result != new_best_result:
                self.best_result = new_best_result
                self.save(update_fields=['best_result'])
                return True
            return False
        except OneKettlebellPressResult.DoesNotExist:
            if self.best_result != 0.0:
                self.best_result = 0.0
                self.save(update_fields=['best_result'])
                return True
            return False

    def __str__(self) -> str:
        return f"{self.player} - Najlepszy One KB Press: {self.best_result:.1f}"
# -*- coding: utf-8 -*-
"""Models definition for Two Kettlebell Press results."""
from typing import Optional, TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę

class TwoKettlebellPressResult(models.Model):
    """Stores the results for the Two Kettlebell Press discipline attempts."""
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="two_kettlebell_press_result"
    )
    result_left_1 = models.FloatField(_("Left Attempt 1"), default=0.0)
    result_right_1 = models.FloatField(_("Right Attempt 1"), default=0.0)
    result_left_2 = models.FloatField(_("Left Attempt 2"), default=0.0)
    result_right_2 = models.FloatField(_("Right Attempt 2"), default=0.0)
    result_left_3 = models.FloatField(_("Left Attempt 3"), default=0.0)
    result_right_3 = models.FloatField(_("Right Attempt 3"), default=0.0)
    position = models.IntegerField(_("Position in Category"), null=True, blank=True)

    class Meta:
        verbose_name = _("Two Kettlebell Press Result")
        verbose_name_plural = _("Two Kettlebell Press Results")
        ordering = ['player__categories', '-position']

    def __str__(self) -> str:
        return f"{self.player} - Two KB Press Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """Calculates the score for a specific attempt (sum of L+R if both > 0)."""
        left = getattr(self, f"result_left_{attempt_number}", 0.0) or 0.0
        right = getattr(self, f"result_right_{attempt_number}", 0.0) or 0.0
        # Suma jeśli obie strony udane (większe od 0)
        return left + right if left > 0 and right > 0 else 0.0

    @property
    def max_score(self) -> float:
        """Returns the maximum score achieved across valid attempts."""
        scores = [
            self.get_attempt_score(1),
            self.get_attempt_score(2),
            self.get_attempt_score(3),
        ]
        return max(scores)

    @property
    def bw_percentage(self) -> Optional[float]:
        """Calculates the max score as a percentage of player's body weight."""
        if self.player.weight and self.player.weight > 0:
            # Używamy max_score (suma L+R) do obliczenia %BW
            return round((self.max_score / self.player.weight) * 100, 2)
        return None

class BestTwoKettlebellPressResult(models.Model):
    """Stores the best combined score (L+R) for Two Kettlebell Press per player."""
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        related_name='best_two_kettlebell_press_result'
    )
    best_result = models.FloatField(_("Best Result (L+R)"), default=0.0)

    class Meta:
        verbose_name = _("Best Two KB Press Result")
        verbose_name_plural = _("Best Two KB Press Results")

    def update_best_result(self) -> bool:
        """
        Updates the best result based on the associated TwoKettlebellPressResult's max_score.
        Returns True if the best result was updated, False otherwise.
        """
        try:
            two_kb_result = self.player.two_kettlebell_press_result
            new_best_result = two_kb_result.max_score # Użyj obliczonej właściwości

            if self.best_result != new_best_result:
                self.best_result = new_best_result
                self.save(update_fields=['best_result'])
                return True
            return False
        except TwoKettlebellPressResult.DoesNotExist:
            if self.best_result != 0.0:
                self.best_result = 0.0
                self.save(update_fields=['best_result'])
                return True
            return False

    def __str__(self) -> str:
        return f"{self.player} - Best Two KB Press: {self.best_result:.1f}"
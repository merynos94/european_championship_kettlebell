# -*- coding: utf-8 -*-
"""Models definition for Kettlebell Squat results."""
from typing import Optional, TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę jeśli Player jest gdzie indziej

class KBSquatResult(models.Model):
    """Stores the results for the Kettlebell Squat discipline attempts."""
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="kb_squat_result"
    )
    result_left_1 = models.FloatField(_("Left Attempt 1"), default=0.0)
    result_right_1 = models.FloatField(_("Right Attempt 1"), default=0.0)
    result_left_2 = models.FloatField(_("Left Attempt 2"), default=0.0)
    result_right_2 = models.FloatField(_("Right Attempt 2"), default=0.0)
    result_left_3 = models.FloatField(_("Left Attempt 3"), default=0.0)
    result_right_3 = models.FloatField(_("Right Attempt 3"), default=0.0)
    position = models.IntegerField(_("Position in Category"), null=True, blank=True)

    class Meta:
        verbose_name = _("KB Squat Result")
        verbose_name_plural = _("KB Squat Results")
        ordering = ['player__categories', '-position']

    def __str__(self) -> str:
        return f"{self.player} - KB Squat Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """
        Calculates the score for a specific attempt (sum of L+R if both > 0).
        Assumes a valid attempt requires lifting with both hands.
        """
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

class BestKBSquatResult(models.Model):
    """Stores the best combined score for KB Squat per player."""
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        related_name='best_kb_squat_result'
    )
    # Przechowuje najlepszy *wynik* (suma L+R), a nie osobno L i R
    best_result = models.FloatField(_("Best Result (L+R)"), default=0.0)

    class Meta:
        verbose_name = _("Best KB Squat Result")
        verbose_name_plural = _("Best KB Squat Results")

    def update_best_result(self) -> bool:
        """
        Updates the best result based on the associated KBSquatResult's max_score.
        Returns True if the best result was updated, False otherwise.
        """
        try:
            # Pobierz powiązany wynik KB Squat
            kbs_result = self.player.kb_squat_result
            new_best_result = kbs_result.max_score # Użyj obliczonej właściwości

            if self.best_result != new_best_result:
                self.best_result = new_best_result
                self.save(update_fields=['best_result'])
                return True
            return False
        except KBSquatResult.DoesNotExist:
            # Jeśli nie ma jeszcze wyniku KBS, zresetuj best_result do 0
            if self.best_result != 0.0:
                self.best_result = 0.0
                self.save(update_fields=['best_result'])
                return True
            return False

    def __str__(self) -> str:
        return f"{self.player} - Best KBS: {self.best_result:.1f}"
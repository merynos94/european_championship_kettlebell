"""Models definition for SeeSawPress results."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass


class SeeSawPressResult(models.Model):
    """Stores the results for the See Saw Press discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player", on_delete=models.CASCADE, verbose_name=_("Player"), related_name="see_saw_press_result"
    )
    result_left_1 = models.FloatField(_("Left Attempt 1"), default=0.0)
    result_right_1 = models.FloatField(_("Right Attempt 1"), default=0.0)
    result_left_2 = models.FloatField(_("Left Attempt 2"), default=0.0)
    result_right_2 = models.FloatField(_("Right Attempt 2"), default=0.0)
    result_left_3 = models.FloatField(_("Left Attempt 3"), default=0.0)
    result_right_3 = models.FloatField(_("Right Attempt 3"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik See Saw Press")
        verbose_name_plural = _("Wyniki See Saw Press")

    def __str__(self) -> str:
        return f"{self.player} - See Saw Press Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """Calculates the score for a specific attempt (L+R if both > 0)."""
        left = getattr(self, f"result_left_{attempt_number}", 0.0) or 0.0
        right = getattr(self, f"result_right_{attempt_number}", 0.0) or 0.0
        # Zmieniona logika? W oryginale było mnożenie przez 3? Zakładam sumę.
        # return (left * 3) + (right * 3) if left > 0 and right > 0 else 0.0
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


class BestSeeSawPressResult(models.Model):
    """Stores the best left and right lifts for See Saw Press per player."""

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.SET_NULL,  # Zmień z CASCADE
        null=True,  # DODAJ null=True
        related_name="best_see_saw_press_result",
    )
    best_left = models.FloatField(_("Best Left"), default=0.0)
    best_right = models.FloatField(_("Best Right"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik See Saw Press")
        verbose_name_plural = _("Najlepsze Wyniki See Saw Press")

    def update_best_result(self) -> bool:
        """Updates best lifts based on the associated SeeSawPressResult."""
        try:
            # Używamy self.player.see_saw_press_result zamiast query
            ssp_result = self.player.see_saw_press_result
            updated = False
            new_best_left = max(
                ssp_result.result_left_1 or 0.0, ssp_result.result_left_2 or 0.0, ssp_result.result_left_3 or 0.0
            )
            new_best_right = max(
                ssp_result.result_right_1 or 0.0, ssp_result.result_right_2 or 0.0, ssp_result.result_right_3 or 0.0
            )

            if self.best_left != new_best_left:
                self.best_left = new_best_left
                updated = True
            if self.best_right != new_best_right:
                self.best_right = new_best_right
                updated = True

            if updated:
                self.save(update_fields=["best_left", "best_right"])
            return updated
        except SeeSawPressResult.DoesNotExist:
            # Jeśli nie ma jeszcze wyniku SSP, resetujemy best
            if self.best_left != 0.0 or self.best_right != 0.0:
                self.best_left = 0.0
                self.best_right = 0.0
                self.save(update_fields=["best_left", "best_right"])
                return True
            return False

    def __str__(self) -> str:
        return f"{self.player} - Best SSP: L {self.best_left}, R {self.best_right}"

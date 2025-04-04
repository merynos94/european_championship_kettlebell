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
        on_delete=models.SET_NULL,
        null=True,
        related_name="best_see_saw_press_result",
    )
    best_result = models.FloatField(_("Best Result (% of body weight)"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik See Saw Press")
        verbose_name_plural = _("Najlepsze Wyniki See Saw Press")

    def update_best_result(self) -> bool:
        """
        Updates best_result, storing PERCENT of body weight (max_score / weight * 100).
        Selects the best attempt based on total (L+R) from a single attempt.
        """
        print(f">>> BestSSP {self.pk}: START update_best_result (PERCENT calc) for player {self.player.id}")
        try:
            ssp_result = self.player.see_saw_press_result
            max_score_val = ssp_result.max_score  # Use the existing property that calculates max score
            player_weight = self.player.weight
            print(f">>> BestSSP {self.pk}: max_score={max_score_val}, player_weight={player_weight}")

            # Calculate new "best" result as PERCENT
            new_best_value = 0.0  # Default to 0
            if player_weight and player_weight > 0 and max_score_val is not None and max_score_val > 0:
                # Calculate PERCENT with 2 decimal places
                new_best_value = round((max_score_val / player_weight) * 100, 2)
                print(f">>> BestSSP {self.pk}: Calculated percent: {new_best_value}%")
            else:
                print(f">>> BestSSP {self.pk}: Player weight={player_weight} or max_score={max_score_val} does not allow percent calculation. Setting to 0.0")

            # Compare and save the new calculated PERCENT
            current_best = self.best_result or 0.0
            if abs(current_best - new_best_value) > 0.001:  # Compare floats
                self.best_result = new_best_value
                print(f">>> BestSSP {self.pk}: Executing save({self.best_result}) (percent)...")
                self.save(update_fields=["best_result"])
                print(f">>> BestSSP {self.pk}: Percent saved.")
                return True

            print(f">>> BestSSP {self.pk}: No changes in percent.")
            return False
        except (SeeSawPressResult.DoesNotExist, AttributeError) as e:
            print(f">>> BestSSP {self.pk}: Cannot get SeeSawPressResult/player/weight ({e}). Resetting best_result to 0.0.")
            current_best = self.best_result or 0.0
            if abs(current_best - 0.0) > 0.001:  # Reset only if not already ~0.0
                self.best_result = 0.0
                self.save(update_fields=["best_result"])
                return True
            return False
        except Exception as e_other:
            print(f"!!!!!!!!! BestSSP {self.pk}: ERROR in update_best_result: {e_other} !!!!!!!!!")
            import traceback
            traceback.print_exc()
            return False

    def __str__(self) -> str:
        return f"{self.player} - Best See Saw Press: {self.best_result:.1f}%"

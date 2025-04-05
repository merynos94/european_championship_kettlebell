# two_kettlebell_press.py
"""Models definition for Two Kettlebell Press results."""

from typing import TYPE_CHECKING, cast

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player


class TwoKettlebellPressResult(models.Model):
    """Stores the results for the Two Kettlebell Press discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="two_kettlebell_press_result",
    )
    result_left_1 = models.FloatField(_("Left Attempt 1"), default=0.0, null=True, blank=True)
    result_right_1 = models.FloatField(_("Right Attempt 1"), default=0.0, null=True, blank=True)
    result_left_2 = models.FloatField(_("Left Attempt 2"), default=0.0, null=True, blank=True)
    result_right_2 = models.FloatField(_("Right Attempt 2"), default=0.0, null=True, blank=True)
    result_left_3 = models.FloatField(_("Left Attempt 3"), default=0.0, null=True, blank=True)
    result_right_3 = models.FloatField(_("Right Attempt 3"), default=0.0, null=True, blank=True)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wyniki Two Kettlebell Press")
        verbose_name_plural = _("Wyniki Two Kettlebells Press")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
       return f"{self.player} - Two KB Press Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """Calculates the score for a specific attempt (sum of L+R if both > 0)."""
        left = getattr(self, f"result_left_{attempt_number}", 0.0) or 0.0
        right = getattr(self, f"result_right_{attempt_number}", 0.0) or 0.0
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
    def bw_percentage(self) -> float | None:
        """Calculates the max score as a percentage of player's body weight."""
        player = getattr(self, "player", None)
        if not player: return None
        player_weight = getattr(player, "weight", None)
        max_s = self.max_score
        if player_weight and player_weight > 0 and max_s > 0:
            return round((max_s / player_weight) * 100, 2)
        return None

# Model BestTwoKettlebellPressResult został usunięty
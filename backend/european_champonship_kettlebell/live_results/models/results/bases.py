from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseDoubleAttemptResult(models.Model):
    """
    Abstract base model for disciplines with 3 L/R attempts.
    """

    result_left_1 = models.FloatField(_("Próba I L"), default=0.0, null=True, blank=True)
    result_right_1 = models.FloatField(_("Próba I R"), default=0.0, null=True, blank=True)
    result_left_2 = models.FloatField(_("Próba II L"), default=0.0, null=True, blank=True)
    result_right_2 = models.FloatField(_("Próba II R"), default=0.0, null=True, blank=True)
    result_left_3 = models.FloatField(_("Próba III L"), default=0.0, null=True, blank=True)
    result_right_3 = models.FloatField(_("Próba III R"), default=0.0, null=True, blank=True)
    position = models.IntegerField(_("Pozycja w kategorii"), null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["player__categories", "-position"]

    def get_attempt_score(self, attempt_number: int) -> float:
        left = getattr(self, f"result_left_{attempt_number}", 0.0) or 0.0
        right = getattr(self, f"result_right_{attempt_number}", 0.0) or 0.0
        return left + right if left > 0 and right > 0 else 0.0

    @property
    def max_score(self) -> float:
        scores = [
            self.get_attempt_score(1),
            self.get_attempt_score(2),
            self.get_attempt_score(3),
        ]
        return max(scores) if scores else 0.0

    @property
    def bw_percentage(self) -> float | None:
        player = getattr(self, "player", None)
        if not player:
            return None
        player_weight = getattr(player, "weight", None)
        max_s = self.max_score
        if isinstance(player_weight, (int, float)) and player_weight > 0 and max_s > 0:
            return round((max_s / player_weight) * 100, 2)
        return None


class BaseSingleAttemptResult(models.Model):
    """
    Abstract base model for disciplines with 3 single-value attempts (e.g., 1RM).
    """

    result_1 = models.FloatField(_("Próba I"), default=0.0, null=True, blank=True)
    result_2 = models.FloatField(_("Próba II"), default=0.0, null=True, blank=True)
    result_3 = models.FloatField(_("Próba III"), default=0.0, null=True, blank=True)
    position = models.IntegerField(_("Pozycja w kategorii"), null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["player__categories", "-position"]

    @property
    def max_result(self) -> float:
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> float | None:
        player = getattr(self, "player", None)
        if not player:
            return None
        player_weight = getattr(player, "weight", None)
        max_res = self.max_result
        if isinstance(player_weight, (int, float)) and player_weight > 0 and max_res > 0:
            return round((max_res / player_weight) * 100, 2)
        return None

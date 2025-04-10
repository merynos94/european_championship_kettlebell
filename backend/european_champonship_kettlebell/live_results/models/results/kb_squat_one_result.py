from django.db import models
from django.utils.translation import gettext_lazy as _

from .bases import BaseSingleAttemptResult  # Changed base class import


class KBSquatResult(BaseSingleAttemptResult):  # Updated base class
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="kb_squat_one_result",
    )

    class Meta(BaseSingleAttemptResult.Meta):  # Updated Meta inheritance
        verbose_name = _("Wynik Kettlebell Squat")
        verbose_name_plural = _("Wyniki Kettlebell Squat")

    def __str__(self) -> str:
        return f"{self.player} - Wyniki KB Squat"

from django.db import models
from django.utils.translation import gettext_lazy as _

from .bases import BaseSingleAttemptResult  # Changed base class import


class TwoKettlebellPressResult(BaseSingleAttemptResult):  # Updated base class
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="two_kettlebell_press_one_result",
    )

    class Meta(BaseSingleAttemptResult.Meta):  # Updated Meta inheritance
        verbose_name = _("Wynik Two Kettlebell Press")
        verbose_name_plural = _("Wyniki Two Kettlebell Press")

    def __str__(self) -> str:
        return f"{self.player} - Wyniki Two KB Press"

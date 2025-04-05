from django.db import models
from django.utils.translation import gettext_lazy as _
from .bases import BaseSingleAttemptResult

class OneKettlebellPressResult(BaseSingleAttemptResult):
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="one_kettlebell_press_result"
    )

    class Meta(BaseSingleAttemptResult.Meta):
        verbose_name = _("Wynik Kettlebell Press")
        verbose_name_plural = _("Wyniki Kettlebell Press")

    def __str__(self) -> str:
        return f"{self.player} - One KB Press Attempts: {self.result_1 or 0}/{self.result_2 or 0}/{self.result_3 or 0}"
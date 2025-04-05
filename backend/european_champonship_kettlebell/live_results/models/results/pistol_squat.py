from django.db import models
from django.utils.translation import gettext_lazy as _
from .bases import BaseSingleAttemptResult

class PistolSquatResult(BaseSingleAttemptResult):
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="pistol_squat_result",
    )

    class Meta(BaseSingleAttemptResult.Meta):
        verbose_name = _("Wynik Pistol Squat")
        verbose_name_plural = _("Wyniki Pistol Squat")

    def __str__(self) -> str:
        return f"{self.player} - Pistol Squat Attempts: {self.result_1 or 0}/{self.result_2 or 0}/{self.result_3 or 0}"
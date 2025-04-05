from django.db import models
from django.utils.translation import gettext_lazy as _

from .bases import BaseSingleAttemptResult


class TGUResult(BaseSingleAttemptResult):
    player = models.OneToOneField(
        "live_results.Player", on_delete=models.CASCADE, verbose_name=_("Zawodnik"), related_name="tgu_result"
    )

    class Meta(BaseSingleAttemptResult.Meta):
        verbose_name = _("Wynik Turkish Get-Up")
        verbose_name_plural = _("Wyniki Turkish Get-Up")

    def __str__(self) -> str:
        return f"{self.player} - TGU Attempts: {self.result_1 or 0}/{self.result_2 or 0}/{self.result_3 or 0}"

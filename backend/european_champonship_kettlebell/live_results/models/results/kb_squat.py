from django.db import models
from django.utils.translation import gettext_lazy as _
from .bases import BaseDoubleAttemptResult

class KBSquatResult(BaseDoubleAttemptResult):
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="kb_squat_result",
    )

    class Meta(BaseDoubleAttemptResult.Meta):
        verbose_name = _("Wynik Kettlebell Squat")
        verbose_name_plural = _("Wyniki Kettlebell Squat")

    def __str__(self) -> str:
        return f"{self.player} - Wyniki KB Squat"

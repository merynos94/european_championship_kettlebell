from django.db import models
from django.utils.translation import gettext_lazy as _

from .bases import BaseDoubleAttemptResult


class SeeSawPressResult(BaseDoubleAttemptResult):
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="see_saw_press_result",
    )

    class Meta(BaseDoubleAttemptResult.Meta):
        verbose_name = _("Wynik See Saw Press")
        verbose_name_plural = _("Wyniki See Saw Press")

    def __str__(self) -> str:
        return f"{self.player} - Wyniki See Saw Press"

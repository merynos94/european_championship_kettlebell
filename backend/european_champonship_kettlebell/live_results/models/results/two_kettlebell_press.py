from django.db import models
from django.utils.translation import gettext_lazy as _
from .bases import BaseDoubleAttemptResult

class TwoKettlebellPressResult(BaseDoubleAttemptResult):
    player = models.OneToOneField(
        "players.Player", # Dostosuj ścieżkę
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="two_kettlebell_press_result",
    )

    class Meta(BaseDoubleAttemptResult.Meta):
        verbose_name = _("Wynik Two Kettlebell Press")
        verbose_name_plural = _("Wyniki Two Kettlebell Press")

    def __str__(self) -> str:
        return f"{self.player} - Wyniki Two KB Press"

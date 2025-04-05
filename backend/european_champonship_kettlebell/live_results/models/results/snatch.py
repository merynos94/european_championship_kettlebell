from django.db import models
from django.utils.translation import gettext_lazy as _

class SnatchResult(models.Model):
    player = models.OneToOneField(
        "players.Player", 
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="snatch_result",
    )
    kettlebell_weight = models.FloatField(_("Waga Kettlebell (kg)"), default=0.0, null=True, blank=True)
    repetitions = models.IntegerField(_("Ilość Powtórzeń"), default=0, null=True, blank=True)
    position = models.IntegerField(_("Pozycja w kategorii"), null=True, blank=True)

    class Meta:
         verbose_name = _("Wynik Snatch")
         verbose_name_plural = _("Wyniki Snatch")
         ordering = ["player__categories", "-position"]

    @property
    def result(self) -> float | None:
        """Calculates Snatch score (weight * reps)."""
        weight = self.kettlebell_weight
        reps = self.repetitions
        if weight is not None and reps is not None and weight > 0 and reps > 0:
            return round(weight * reps, 1)
        return None

    def __str__(self) -> str:
        score = self.result
        return f"{self.player} - Snatch: {score if score is not None else 'N/A'}"
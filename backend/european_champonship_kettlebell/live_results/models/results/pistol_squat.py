"""Model definition for PistolSquatResult."""


from django.db import models
from django.utils.translation import gettext_lazy as _



class PistolSquatResult(models.Model):
    """Stores the results for the Pistol Squat discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="pistol_squat_result",
    )
    result_1 = models.FloatField(_("Próba I"), default=0.0, null=True, blank=True)
    result_2 = models.FloatField(_("Próba II"), default=0.0, null=True, blank=True)
    result_3 = models.FloatField(_("Próba III"), default=0.0, null=True, blank=True)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Pistol Squat")
        verbose_name_plural = _("Wyniki Pistol Squat")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
        # Użyj 'or 0' do wyświetlania, jeśli wartość jest None
        return f"{self.player} - Pistol Squat Attempts: {self.result_1 or 0}/{self.result_2 or 0}/{self.result_3 or 0}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        player = getattr(self, "player", None)
        if not player:
            return None
        player_weight = getattr(player, "weight", None)

        max_res = self.max_result
        if player_weight and player_weight > 0 and max_res > 0:
            return round((max_res / player_weight) * 100, 2)
        return None

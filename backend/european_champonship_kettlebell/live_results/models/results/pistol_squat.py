"""Model definition for PistolSquatResult."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass  # Dostosuj ścieżkę jeśli Player jest gdzie indziej


class PistolSquatResult(models.Model):
    """Stores the results for the Pistol Squat discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player",  # Użyj stringa dla uniknięcia importów
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="pistol_squat_result",
    )
    result_1 = models.FloatField(_("Próba I"), default=0.0)
    result_2 = models.FloatField(_("Próba II"), default=0.0)
    result_3 = models.FloatField(_("Próba III"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Pistol Squat")
        verbose_name_plural = _("Wyniki Pistol Squat")
        ordering = ["player__categories", "-position"]  # Sortowanie wg pozycji

    def __str__(self) -> str:
        return f"{self.player} - Pistol Squat Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @max_result.setter
    def max_result(self, value: float) -> None:
        """Sets the maximum result by updating the first attempt."""
        # You need to decide how setting max_result should behave
        # This is one implementation - it sets result_1 to the provided value
        self.result_1 = value

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        # Upewnij się, że player.weight nie jest None i jest większe od 0
        if self.player.weight and self.player.weight > 0:
            return round((self.max_result / self.player.weight) * 100, 2)
        return None


from typing import TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _
# Zaimportuj model PistolSquatResult
from .pistol_squat import PistolSquatResult # Dostosuj ścieżkę

if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę

class BestPistolSquatResult(models.Model):
    """Stores the best Pistol Squat result per player."""
    player = models.OneToOneField['Player'](
        'Player',
        on_delete=models.CASCADE,
        related_name='best_pistol_squat_result' # Ważne: unikalna related_name
    )
    best_result = models.FloatField(_("Najlepszy Wynik Pistol Squat"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Pistol Squat")
        verbose_name_plural = _("Najlepsze Wyniki Pistol Squat")

    def update_best_result(self) -> bool:
        """Updates the best result based on the associated PistolSquatResult's max_result."""
        try:
            pistol_result = self.player.pistol_squat_result # Użyj related_name z PistolSquatResult
            new_best_result = pistol_result.max_result

            if self.best_result != new_best_result:
                self.best_result = new_best_result
                self.save(update_fields=['best_result'])
                return True
            return False
        except PistolSquatResult.DoesNotExist:
            if self.best_result != 0.0:
                self.best_result = 0.0
                self.save(update_fields=['best_result'])
                return True
            return False

    def __str__(self) -> str:
        return f"{self.player} - Najlepszy Pistol Squat: {self.best_result:.1f}"
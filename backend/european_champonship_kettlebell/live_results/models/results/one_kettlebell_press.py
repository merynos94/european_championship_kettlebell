"""Model definition for OneKettlebellPressResult."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass


class OneKettlebellPressResult(models.Model):
    """Stores the results for the One Kettlebell Press discipline attempts (1RM)."""

    player = models.OneToOneField(
        "Player", on_delete=models.CASCADE, verbose_name=_("Player"), related_name="one_kettlebell_press_result"
    )
    result_1 = models.FloatField(_("Próba I Kettlebell Press"), default=0.0)
    result_2 = models.FloatField(_("Próba II Kettlebell Press"), default=0.0)
    result_3 = models.FloatField(_("Próba III Kettlebell Press"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Kettlebell Press")
        verbose_name_plural = _("Wyniki Kettlebell Press")
        ordering = ["player__categories", "-position"]  # Sortowanie wg pozycji

    def __str__(self) -> str:
        return f"{self.player} - One KB Press Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        if self.player.weight and self.player.weight > 0:
            return round((self.max_result / self.player.weight) * 100, 2)
        return None


class BestOneKettlebellPressResult(models.Model):
    """Stores the best One Kettlebell Press result per player."""

    player = models.OneToOneField("Player", on_delete=models.CASCADE, related_name="best_one_kettlebell_press_result")
    best_result = models.FloatField(_("Best One KB Press Result"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Kettlebell Press")
        verbose_name_plural = _("Najlepsze Wyniki Kettlebell Press")

    def update_best_result(self) -> bool:
        """
        Aktualizuje best_result, zapisując PROCENT masy ciała (max_result / waga * 100).
        """
        print(f">>> BestOKBP {self.pk}: START update_best_result (PERCENT calc) dla player {self.player.id}")
        try:
            press_result = self.player.one_kettlebell_press_result
            max_res = press_result.max_result  # Maksymalny ciężar
            player_weight = self.player.weight
            print(f">>> BestOKBP {self.pk}: max_res={max_res}, player_weight={player_weight}")

            # Oblicz nowy "najlepszy" wynik jako PROCENT
            new_best_value = 0.0  # Domyślnie 0
            if player_weight and player_weight > 0 and max_res is not None and max_res > 0:
                # Oblicz PROCENT, np. z 2 miejscami po przecinku
                new_best_value = round((max_res / player_weight) * 100, 2)  # Mnożymy przez 100
                print(f">>> BestOKBP {self.pk}: Obliczony procent: {new_best_value}%")
            else:
                print(
                    f">>> BestOKBP {self.pk}: Waga gracza={player_weight} lub max_res={max_res} nie pozwala na obliczenie procentu. Ustawiam na 0.0"
                )

            # Porównaj i zapisz nowy obliczony PROCENT
            current_best = self.best_result or 0.0
            if abs(current_best - new_best_value) > 0.001:  # Porównanie float
                self.best_result = new_best_value
                print(f">>> BestOKBP {self.pk}: Wykonuję save({self.best_result}) (procent)...")
                self.save(update_fields=["best_result"])
                print(f">>> BestOKBP {self.pk}: Zapisano procent.")
                return True

            print(f">>> BestOKBP {self.pk}: Brak zmian w procencie.")
            return False
        except (OneKettlebellPressResult.DoesNotExist, AttributeError) as e:
            print(
                f">>> BestOKBP {self.pk}: Nie można pobrać OKBPResult/gracza/wagi ({e}). Resetuję best_result do 0.0."
            )
            current_best = self.best_result or 0.0
            if abs(current_best - 0.0) > 0.001:  # Resetuj tylko jeśli nie jest już ~0.0
                self.best_result = 0.0
                self.save(update_fields=["best_result"])
                return True
            return False
        except Exception as e_other:
            print(f"!!!!!!!!! BestOKBP {self.pk}: BŁĄD w update_best_result: {e_other} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            return False

    def __str__(self) -> str:
        return f"{self.player} - Najlepszy One KB Press: {self.best_result:.1f}"

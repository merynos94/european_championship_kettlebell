"""Model definition for TGUResult."""

from typing import TYPE_CHECKING, cast

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass  # Adjust this import path to match your project structure


class TGUResult(models.Model):
    """Stores the results for the Turkish Get-Up discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player", on_delete=models.CASCADE, verbose_name=_("Player"), related_name="tgu_result"
    )
    result_1 = models.FloatField(_("Podejście 1"), default=0.0)
    result_2 = models.FloatField(_("Podejście 2"), default=0.0)
    result_3 = models.FloatField(_("Podejście 3"), default=0.0)
    position = models.IntegerField(_("Miejsce w kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Turkish Get-Up")
        verbose_name_plural = _("Wyniki Turkish Get-Up")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
        return f"{self.player} - TGU Attempts: {self.result_1}/{self.result_2}/{self.result_3}"

    @property
    def max_result(self) -> float:
        """Returns the maximum weight lifted across attempts."""
        return max(self.result_1 or 0.0, self.result_2 or 0.0, self.result_3 or 0.0)

    @max_result.setter
    def max_result(self, value: float) -> None:
        """Sets the maximum result to one of the attempts."""
        # Convert None values to 0.0 for comparison
        r1 = self.result_1 or 0.0
        r2 = self.result_2 or 0.0
        r3 = self.result_3 or 0.0

        # Determine which result to update based on current values
        if r1 <= r2 and r1 <= r3:
            self.result_1 = value
        elif r2 <= r1 and r2 <= r3:
            self.result_2 = value
        else:
            self.result_3 = value

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max result as a percentage of player's body weight."""
        if TYPE_CHECKING:
            from ..player import Player

            player = cast(Player, self.player)
        else:
            player = self.player

        if player.weight and player.weight > 0:
            return round((self.max_result / player.weight) * 100, 2)
        return None


class BestTGUResult(models.Model):
    """Stores the best TGU result per player."""

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.CASCADE,
        related_name="best_tgu_result",  # Ważne: unikalna related_name
    )
    best_result = models.FloatField(_("Najlepszy Wynik TGU"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Turkish Get-Up")
        verbose_name_plural = _("Najlepsze Wyniki Turkish Get-Up")

    def update_best_result(self) -> bool:
        """
        Aktualizuje best_result, zapisując PROCENT masy ciała (max_result / waga * 100).
        """
        print(f">>> BestTGU {self.pk}: START update_best_result (PERCENT calc) dla player {self.player.id}")
        try:
            tgu_result = self.player.tgu_result
            max_res = tgu_result.max_result  # Maksymalny ciężar
            player_weight = self.player.weight
            print(f">>> BestTGU {self.pk}: max_res={max_res}, player_weight={player_weight}")

            # Oblicz nowy "najlepszy" wynik jako PROCENT
            new_best_value = 0.0  # Domyślnie 0
            if player_weight and player_weight > 0 and max_res is not None and max_res > 0:
                # Oblicz PROCENT, np. z 2 miejscami po przecinku
                new_best_value = round((max_res / player_weight) * 100, 2)  # Mnożymy przez 100
                print(f">>> BestTGU {self.pk}: Obliczony procent: {new_best_value}%")
            else:
                print(
                    f">>> BestTGU {self.pk}: Waga gracza={player_weight} lub max_res={max_res} nie pozwala na obliczenie procentu. Ustawiam na 0.0"
                )

            # Porównaj i zapisz nowy obliczony PROCENT
            current_best = self.best_result or 0.0
            # Używamy małej tolerancji dla porównań float
            if abs(current_best - new_best_value) > 0.001:  # Porównanie float
                self.best_result = new_best_value
                print(f">>> BestTGU {self.pk}: Wykonuję save({self.best_result}) (procent)...")
                self.save(update_fields=["best_result"])
                print(f">>> BestTGU {self.pk}: Zapisano procent.")
                return True

            print(f">>> BestTGU {self.pk}: Brak zmian w procencie.")
            return False
        except (TGUResult.DoesNotExist, AttributeError) as e:
            print(f">>> BestTGU {self.pk}: Nie można pobrać TGUResult/gracza/wagi ({e}). Resetuję best_result do 0.0.")
            current_best = self.best_result or 0.0  # Sprawdź przed resetem
            if abs(current_best - 0.0) > 0.001:  # Resetuj tylko jeśli nie jest już ~0.0
                self.best_result = 0.0
                self.save(update_fields=["best_result"])
                return True
            return False
        except Exception as e_other:
            print(f"!!!!!!!!! BestTGU {self.pk}: BŁĄD w update_best_result: {e_other} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            return False

    def __str__(self) -> str:
        return f"{self.player} - Najlepszy TGU: {self.best_result:.1f}"

"""Models definition for Two Kettlebell Press results."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass  # Dostosuj ścieżkę


class TwoKettlebellPressResult(models.Model):
    """Stores the results for the Two Kettlebell Press discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player",  # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="two_kettlebell_press_result",
    )
    result_left_1 = models.FloatField(_("Left Attempt 1"), default=0.0)
    result_right_1 = models.FloatField(_("Right Attempt 1"), default=0.0)
    result_left_2 = models.FloatField(_("Left Attempt 2"), default=0.0)
    result_right_2 = models.FloatField(_("Right Attempt 2"), default=0.0)
    result_left_3 = models.FloatField(_("Left Attempt 3"), default=0.0)
    result_right_3 = models.FloatField(_("Right Attempt 3"), default=0.0)
    position = models.IntegerField(_("Pozycja w Kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wyniki Two Kettlebell Press")
        verbose_name_plural = _("Wyniki Two Kettlebells Press")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
        return f"{self.player} - Two KB Press Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """Calculates the score for a specific attempt (sum of L+R if both > 0)."""
        left = getattr(self, f"result_left_{attempt_number}", 0.0) or 0.0
        right = getattr(self, f"result_right_{attempt_number}", 0.0) or 0.0
        # Suma jeśli obie strony udane (większe od 0)
        return left + right if left > 0 and right > 0 else 0.0

    @property
    def max_score(self) -> float:
        """Returns the maximum score achieved across valid attempts."""
        scores = [
            self.get_attempt_score(1),
            self.get_attempt_score(2),
            self.get_attempt_score(3),
        ]
        return max(scores)

    @property
    def bw_percentage(self) -> float | None:
        """Calculates the max score as a percentage of player's body weight."""
        if self.player.weight and self.player.weight > 0:
            # Używamy max_score (suma L+R) do obliczenia %BW
            return round((self.max_score / self.player.weight) * 100, 2)
        return None


class BestTwoKettlebellPressResult(models.Model):
    """Stores the best combined score (L+R) for Two Kettlebell Press per player."""

    player = models.OneToOneField["Player"](
        "Player",  # Użyj stringa
        on_delete=models.SET_NULL,  # Zmień z CASCADE
        null=True,  # DODAJ null=True
        related_name="best_two_kettlebell_press_result",
    )
    best_result = models.FloatField(_("Najlepszy Wynik (L+R)"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Two Kettlebell Press")
        verbose_name_plural = _("Najlepsze Wyniki Two Kettlebells Press")

        # W pliku two_kettlebell_press.py (lub gdziekolwiek jest model BestTwoKettlebellPressResult)
        # Wewnątrz klasy BestTwoKettlebellPressResult

        # ZASTĄP obecną metodę update_best_result poniższą:

    def update_best_result(self) -> bool:
        """
        Aktualizuje best_result, zapisując PROCENT masy ciała (max_score / waga * 100).
        """
        print(f">>> BestTKBP {self.pk}: START update_best_result (PERCENT calc) dla player {self.player.id}")
        try:
            two_kb_result = self.player.two_kettlebell_press_result
            max_score_val = two_kb_result.max_score  # Maksymalny wynik (suma L+R)
            player_weight = self.player.weight
            print(f">>> BestTKBP {self.pk}: max_score={max_score_val}, player_weight={player_weight}")

            # Oblicz nowy "najlepszy" wynik jako PROCENT
            new_best_value = 0.0
            if player_weight and player_weight > 0 and max_score_val is not None and max_score_val > 0:
                new_best_value = round((max_score_val / player_weight) * 100, 2)  # Mnożymy przez 100
                print(f">>> BestTKBP {self.pk}: Obliczony procent: {new_best_value}%")
            else:
                print(
                    f">>> BestTKBP {self.pk}: Waga gracza={player_weight} lub max_score={max_score_val} nie pozwala na obliczenie procentu. Ustawiam na 0.0"
                )

            # Porównaj i zapisz nowy obliczony PROCENT
            current_best = self.best_result or 0.0
            if abs(current_best - new_best_value) > 0.001:  # Porównanie float
                self.best_result = new_best_value
                print(f">>> BestTKBP {self.pk}: Wykonuję save({self.best_result}) (procent)...")
                self.save(update_fields=["best_result"])
                print(f">>> BestTKBP {self.pk}: Zapisano procent.")
                return True

            print(f">>> BestTKBP {self.pk}: Brak zmian w procencie.")
            return False
        except (TwoKettlebellPressResult.DoesNotExist, AttributeError) as e:
            print(
                f">>> BestTKBP {self.pk}: Nie można pobrać TKBPResult/gracza/wagi ({e}). Resetuję best_result do 0.0."
            )
            current_best = self.best_result or 0.0
            if abs(current_best - 0.0) > 0.001:
                self.best_result = 0.0
                self.save(update_fields=["best_result"])
                return True
            return False
        except Exception as e_other:
            print(f"!!!!!!!!! BestTKBP {self.pk}: BŁĄD w update_best_result: {e_other} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            return False

    def __str__(self) -> str:
        return f"{self.player} - Best Two KB Press: {self.best_result:.1f}"

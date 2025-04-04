"""Models definition for Kettlebell Squat results."""

from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass  # Dostosuj ścieżkę jeśli Player jest gdzie indziej


class KBSquatResult(models.Model):
    """Stores the results for the Kettlebell Squat discipline attempts."""

    player = models.OneToOneField["Player"](
        "Player",  # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="kb_squat_result",
    )
    result_left_1 = models.FloatField(_("Próba I L"), default=0.0)
    result_right_1 = models.FloatField(_("Próba I R"), default=0.0)
    result_left_2 = models.FloatField(_("Próba II L"), default=0.0)
    result_right_2 = models.FloatField(_("Próba II R"), default=0.0)
    result_left_3 = models.FloatField(_("Próba III L"), default=0.0)
    result_right_3 = models.FloatField(_("Próba III R"), default=0.0)
    position = models.IntegerField(_("Pozycja w kategorii"), null=True, blank=True)

    class Meta:
        verbose_name = _("Wynik Kettllebell Squat")
        verbose_name_plural = _("Wyniki Kettlebell Squat")
        ordering = ["player__categories", "-position"]

    def __str__(self) -> str:
        return f"{self.player} - KB Squat Attempts"

    def get_attempt_score(self, attempt_number: int) -> float:
        """
        Calculates the score for a specific attempt (sum of L+R if both > 0).
        Assumes a valid attempt requires lifting with both hands.
        """
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


class BestKBSquatResult(models.Model):
    """Stores the best combined score for KB Squat per player."""

    player = models.OneToOneField["Player"](
        "Player",  # Użyj stringa
        on_delete=models.SET_NULL,  # Zmień z CASCADE
        null=True,  # DODAJ null=True
        related_name="best_kb_squat_result",
    )
    # Przechowuje najlepszy *wynik* (suma L+R), a nie osobno L i R
    best_result = models.FloatField(_("Najlepszy Wynik (L+R)"), default=0.0)

    class Meta:
        verbose_name = _("Najlepszy Wynik Kettlebell Squat")
        verbose_name_plural = _("Najlepsze Wyniki Kettlebell Squat")

    def update_best_result(self) -> bool:
        """
        Aktualizuje best_result, zapisując PROCENT masy ciała (max_score / waga * 100).
        """
        print(f">>> BestKBS {self.pk}: START update_best_result (PERCENT calc) dla player {self.player.id}")
        try:
            kbs_result = self.player.kb_squat_result
            max_score_val = kbs_result.max_score  # Maksymalny wynik (suma L+R)
            player_weight = self.player.weight
            print(f">>> BestKBS {self.pk}: max_score={max_score_val}, player_weight={player_weight}")

            # Oblicz nowy "najlepszy" wynik jako PROCENT
            new_best_value = 0.0
            if player_weight and player_weight > 0 and max_score_val is not None and max_score_val > 0:
                new_best_value = round((max_score_val / player_weight) * 100, 2)  # Mnożymy przez 100
                print(f">>> BestKBS {self.pk}: Obliczony procent: {new_best_value}%")
            else:
                print(
                    f">>> BestKBS {self.pk}: Waga gracza={player_weight} lub max_score={max_score_val} nie pozwala na obliczenie procentu. Ustawiam na 0.0"
                )

            # Porównaj i zapisz nowy obliczony PROCENT
            current_best = self.best_result or 0.0
            if abs(current_best - new_best_value) > 0.001:  # Porównanie float
                self.best_result = new_best_value
                print(f">>> BestKBS {self.pk}: Wykonuję save({self.best_result}) (procent)...")
                self.save(update_fields=["best_result"])
                print(f">>> BestKBS {self.pk}: Zapisano procent.")
                return True

            print(f">>> BestKBS {self.pk}: Brak zmian w procencie.")
            return False
        except (KBSquatResult.DoesNotExist, AttributeError) as e:
            print(
                f">>> BestKBS {self.pk}: Nie można pobrać KBSquatResult/gracza/wagi ({e}). Resetuję best_result do 0.0."
            )
            current_best = self.best_result or 0.0
            if abs(current_best - 0.0) > 0.001:
                self.best_result = 0.0
                self.save(update_fields=["best_result"])
                return True
            return False
        except Exception as e_other:
            print(f"!!!!!!!!! BestKBS {self.pk}: BŁĄD w update_best_result: {e_other} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            return False

    def __str__(self) -> str:
        return f"{self.player} - Najlepszy Kettllebel Squat: {self.best_result:.1f}"

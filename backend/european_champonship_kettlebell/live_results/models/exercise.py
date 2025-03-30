from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Exercise(models.Model):
    """
    Exercise model representing a specific exercise performed by an athlete in a category.
    Contains all exercise data and methods for calculating scores.
    """

    athlete = models.ForeignKey("Athlete", on_delete=models.CASCADE, related_name="exercises", verbose_name="Zawodnik")
    exercise_type = models.ForeignKey(
        "ExerciseType", on_delete=models.CASCADE, related_name="exercises", verbose_name="Typ ćwiczenia"
    )

    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="category_exercises",  # Zmieniona nazwa relacji zwrotnej
        verbose_name="Kategoria",
    )

    # === Fields for Snatch ===
    kettlebell_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Waga odważnika [kg]",
    )
    repetitions = models.PositiveIntegerField(default=0, verbose_name="Liczba powtórzeń")

    # === Fields for multi-attempt exercises (TGU, Press, Squat) ===
    attempt1_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 1 [kg]",
    )
    attempt2_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 2 [kg]",
    )
    attempt3_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 3 [kg]",
    )

    # === Metadata ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.athlete} - {self.exercise_type} ({self.category})"

    class Meta:
        verbose_name = "Ćwiczenie"
        verbose_name_plural = "Ćwiczenia"
        unique_together = [["athlete", "exercise_type", "category"]]

    # === Helper methods ===

    def get_best_attempt(self):
        """Return the best attempt weight from the three attempts."""
        return max(self.attempt1_weight, self.attempt2_weight, self.attempt3_weight)

    # === Score calculation methods ===

    def calculate_score(self):
        """
        Calculate exercise score based on the calculation method defined in exercise type.
        """
        # Bezpiecznie pobierz calculation_method z exercise_type
        try:
            calculation_method = self.exercise_type.calculation_method
        except AttributeError:
            # Jeśli nie można uzyskać dostępu do calculation_method,
            # sprawdź czy istnieje pole name w exercise_type i użyj go do określenia metody
            if hasattr(self.exercise_type, "name"):
                exercise_name = self.exercise_type.name.lower()
                if "snatch" in exercise_name:
                    calculation_method = "weight_x_reps"
                elif any(x in exercise_name for x in ["turkish", "tgu", "press", "squat"]):
                    calculation_method = "weight_to_body"
                else:
                    calculation_method = "best_attempt"
            else:
                # Domyślna metoda, jeśli nie można określić po nazwie
                calculation_method = "best_attempt"

        # Obliczanie wyniku na podstawie metody
        if calculation_method == "weight_x_reps":
            # Dla Snatch: kettlebell weight × repetitions
            return float(self.kettlebell_weight) * self.repetitions

        elif calculation_method == "weight_to_body":
            # Dla ćwiczeń z relacją wagi do masy ciała (TGU, Press)
            best_attempt = float(self.get_best_attempt())

            # Bezpiecznie pobierz body_weight z athlete
            try:
                body_weight = float(self.athlete.body_weight)
            except (AttributeError, ValueError):
                # Jeśli nie można uzyskać dostępu do body_weight, zwróć samą wartość próby
                return best_attempt

            if best_attempt > 0 and body_weight > 0:
                return best_attempt / body_weight
            return 0

        elif calculation_method == "best_attempt":
            # Po prostu zwróć najlepszą próbę
            return float(self.get_best_attempt())

        # Możliwość rozszerzenia o inne metody kalkulacji
        return 0

    # === Update methods ===

    def update_snatch(self, weight, repetitions):
        """Update Snatch results."""
        self.kettlebell_weight = Decimal(str(weight))
        self.repetitions = repetitions
        self.save(update_fields=["kettlebell_weight", "repetitions"])
        return self

    def update_attempt(self, attempt_number, weight):
        """Update a specific attempt weight."""
        if attempt_number not in (1, 2, 3):
            raise ValueError("Attempt number must be 1, 2, or 3.")

        field_name = f"attempt{attempt_number}_weight"
        setattr(self, field_name, Decimal(str(weight)))
        self.save(update_fields=[field_name])
        return self

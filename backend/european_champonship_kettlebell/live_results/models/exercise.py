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
    # Add these fields to your Exercise model
    attempt1_weight_left = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 1 - lewa ręka [kg]",
    )
    attempt1_weight_right = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 1 - prawa ręka [kg]",
    )
    attempt2_weight_left = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 2 - lewa ręka [kg]",
    )
    attempt2_weight_right = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 2 - prawa ręka [kg]",
    )
    attempt3_weight_left = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 3 - lewa ręka [kg]",
    )
    attempt3_weight_right = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Próba 3 - prawa ręka [kg]",
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
        """Calculate exercise score based on the calculation method."""
        calculation_method = self.exercise_type.calculation_method

        if calculation_method == "athlete_weight_x_reps":
            return float(self.kettlebell_weight) * self.repetitions

        elif calculation_method == "weight_to_percent_body":
            best_attempt = float(self.get_best_attempt())
            body_weight = float(self.athlete.body_weight) if self.athlete.body_weight else 1
            return best_attempt / body_weight if body_weight > 0 else 0

        elif calculation_method == "best_attempt":
            return float(self.get_best_attempt())

        elif calculation_method == "weight_to_percent_body_two_hands":
            # Calculate best combined weight for each attempt
            attempt1 = float(self.attempt1_weight_left) + float(self.attempt1_weight_right)
            attempt2 = float(self.attempt2_weight_left) + float(self.attempt2_weight_right)
            attempt3 = float(self.attempt3_weight_left) + float(self.attempt3_weight_right)
            best_attempt = max(attempt1, attempt2, attempt3)

            body_weight = float(self.athlete.body_weight) if self.athlete.body_weight else 1
            return best_attempt / body_weight if body_weight > 0 else 0

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

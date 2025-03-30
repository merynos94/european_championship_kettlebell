from django.db import models

from .category import Category

# Define calculation methods constant
CALCULATION_METHODS = [
    ("athlete_weight_x_reps", "Waga × Powtórzenia"),
    ("weight_to_percent_body", "Stosunek do %masy ciała"),
    ("best_attempt", "Najlepsza próba"),
    ("weight_to_percent_body_two_hands", "Stosunek do %masy ciała (dwie ręce)"),
]


class ExerciseType(models.Model):
    """
    ExerciseType model representing the different types of exercises in the competition.
    Defines how scores are calculated for each exercise type.
    """

    name = models.CharField(max_length=100, verbose_name="Nazwa ćwiczenia")
    calculation_method = models.CharField(
        max_length=35,  # Increased to accommodate longest value
        choices=CALCULATION_METHODS,
        default="athlete_weight_x_reps",
        verbose_name="Metoda obliczania wyniku"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktywny")
    attempts_count = models.PositiveSmallIntegerField(default=1, verbose_name="Liczba prób")
    categories = models.ManyToManyField(
        Category,
        related_name="exercise_types",
        verbose_name="Kategorie",
        blank=True,
        help_text="Kategorie, w których to ćwiczenie jest używane",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Typ ćwiczenia"
        verbose_name_plural = "Typy ćwiczeń"
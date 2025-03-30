from django.db import models

from .category import Category


class ExerciseType(models.Model):
    """
    ExerciseType model representing the different types of exercises in the competition.
    Defines how scores are calculated for each exercise type.
    """

    CALCULATION_METHODS = [
        ("weight_x_reps", "Waga × Powtórzenia"),
        ("weight_to_body", "Stosunek do masy ciała"),
        ("best_attempt", "Najlepsza próba"),
        ("custom", "Niestandardowa metoda"),
    ]

    name = models.CharField(max_length=100, verbose_name="Nazwa ćwiczenia")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    calculation_method = models.CharField(
        max_length=20, choices=CALCULATION_METHODS, default="weight_x_reps", verbose_name="Metoda obliczania wyniku"
    )
    attempts_count = models.PositiveSmallIntegerField(default=1, verbose_name="Liczba prób")
    is_active = models.BooleanField(default=True, verbose_name="Aktywne")
    categories = models.ManyToManyField(
        Category,
        related_name="exercises",
        verbose_name="Kategorie",
        blank=True,
        help_text="Kategorie, w których to ćwiczenie jest używane",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Typ ćwiczenia"
        verbose_name_plural = "Typy ćwiczeń"

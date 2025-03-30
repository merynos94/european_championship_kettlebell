# from django.db import models
# from django.core.validators import MinValueValidator
# from decimal import Decimal
#
#
# class Club(models.Model):
#     """Model reprezentujący klub sportowy zawodnika"""
#     name = models.CharField(max_length=150, verbose_name="Nazwa klubu")
#     address = models.TextField(blank=True, null=True, verbose_name="Adres")
#     contact = models.CharField(max_length=200, blank=True, null=True, verbose_name="Kontakt")
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Klub"
#         verbose_name_plural = "Kluby"
#         ordering = ['name']
#
#
# class Category(models.Model):
#     """
#     Model reprezentujący kategorię zawodów.
#     Przykładowo: kategoria wagowa, wiekowa, itp.
#     """
#     name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
#     description = models.TextField(blank=True, null=True, verbose_name="Opis")
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Kategoria"
#         verbose_name_plural = "Kategorie"
#         ordering = ['name']
#
#
# class ExerciseType(models.Model):
#     """
#     Model reprezentujący typ ćwiczenia/konkurencji.
#     Pozwala na elastyczne definiowanie różnych konkurencji.
#     """
#     CALCULATION_METHODS = [
#         ('weight_x_reps', 'Waga × Powtórzenia'),
#         ('weight_to_body', 'Stosunek do masy ciała'),
#         ('best_attempt', 'Najlepsza próba'),
#         ('custom', 'Niestandardowa metoda')
#     ]
#
#     name = models.CharField(max_length=100, verbose_name="Nazwa ćwiczenia")
#     description = models.TextField(blank=True, null=True, verbose_name="Opis")
#     calculation_method = models.CharField(
#         max_length=20,
#         choices=CALCULATION_METHODS,
#         default='weight_x_reps',
#         verbose_name="Metoda obliczania wyniku"
#     )
#     attempts_count = models.PositiveSmallIntegerField(
#         default=1,
#         verbose_name="Liczba prób"
#     )
#     is_active = models.BooleanField(default=True, verbose_name="Aktywne")
#     categories = models.ManyToManyField(
#         Category,
#         related_name='exercises',
#         verbose_name="Kategorie",
#         blank=True,
#         help_text="Kategorie, w których to ćwiczenie jest używane"
#     )
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = "Typ ćwiczenia"
#         verbose_name_plural = "Typy ćwiczeń"
#
#
# class Athlete(models.Model):
#     """
#     Model reprezentujący zawodnika.
#     Zawiera podstawowe dane osobowe.
#     """
#     first_name = models.CharField(max_length=100, verbose_name="Imię")
#     last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
#     club = models.ForeignKey(
#         Club,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="athletes",
#         verbose_name="Klub"
#     )
#     body_weight = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))],
#         verbose_name="Waga ciała [kg]"
#     )
#     categories = models.ManyToManyField(
#         Category,
#         through='AthleteCategory',
#         related_name="athletes",
#         verbose_name="Kategorie"
#     )
#     notes = models.TextField(blank=True, null=True, verbose_name="Uwagi")
#
#     def __str__(self):
#         club_name = self.club.name if self.club else "Brak klubu"
#         return f"{self.first_name} {self.last_name} ({club_name})"
#
#     class Meta:
#         verbose_name = "Zawodnik"
#         verbose_name_plural = "Zawodnicy"
#         ordering = ['last_name', 'first_name']
#
#     def get_total_points(self, category=None):
#         """
#         Oblicza łączną liczbę punktów zawodnika w danej kategorii.
#         Mniejsza liczba punktów oznacza lepszy wynik.
#         """
#         category_enrollments = self.category_enrollments.filter(
#             category=category) if category else self.category_enrollments.all()
#         total = 0
#
#         for enrollment in category_enrollments:
#             # Suma punktów z poszczególnych kategorii
#             total += enrollment.points
#
#             # Uwzględnienie dogrywki
#             if enrollment.tiebreaker:
#                 total -= 0.5
#
#         return total
#
#
# class AthleteCategory(models.Model):
#     """
#     Model łączący zawodnika z kategorią.
#     Zawiera informacje o punktach i dogrywkach.
#     """
#     athlete = models.ForeignKey(
#         Athlete,
#         on_delete=models.CASCADE,
#         related_name="category_enrollments",
#         verbose_name="Zawodnik"
#     )
#     category = models.ForeignKey(
#         Category,
#         on_delete=models.CASCADE,
#         related_name="athlete_enrollments",
#         verbose_name="Kategoria"
#     )
#     points = models.DecimalField(
#         max_digits=5,
#         decimal_places=1,
#         default=0,
#         verbose_name="Punkty"
#     )
#     tiebreaker = models.BooleanField(
#         default=False,
#         verbose_name="Dogrywka (-0.5 pkt)"
#     )
#     place = models.PositiveSmallIntegerField(
#         null=True,
#         blank=True,
#         verbose_name="Miejsce"
#     )
#
#     def __str__(self):
#         return f"{self.athlete} - {self.category}"
#
#     class Meta:
#         verbose_name = "Zawodnik w kategorii"
#         verbose_name_plural = "Zawodnicy w kategoriach"
#         unique_together = [['athlete', 'category']]
#
#     def save(self, *args, **kwargs):
#         """
#         Nadpisana metoda save() do automatycznego ustawiania punktów na podstawie zajętego miejsca,
#         jeśli ustawiono miejsce (place).
#         """
#         if self.place is not None and self.place > 0:
#             self.points = self.place
#         super().save(*args, **kwargs)
#
#
# class Exercise(models.Model):
#     """
#     Model reprezentujący konkretne ćwiczenie wykonane przez zawodnika.
#     """
#     athlete = models.ForeignKey(
#         Athlete,
#         on_delete=models.CASCADE,
#         related_name="exercises",
#         verbose_name="Zawodnik"
#     )
#     exercise_type = models.ForeignKey(
#         ExerciseType,
#         on_delete=models.CASCADE,
#         related_name="exercises",
#         verbose_name="Typ ćwiczenia"
#     )
#     category = models.ForeignKey(
#         Category,
#         on_delete=models.CASCADE,
#         related_name="exercises",
#         verbose_name="Kategoria"
#     )
#
#     # === Pola dla Snatch ===
#     kettlebell_weight = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         validators=[MinValueValidator(Decimal('0.00'))],
#         verbose_name="Waga odważnika [kg]"
#     )
#     repetitions = models.PositiveIntegerField(
#         default=0,
#         verbose_name="Liczba powtórzeń"
#     )
#
#     # === Pola dla ćwiczeń z wieloma próbami (TGU, Press, Squat) ===
#     attempt1_weight = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         validators=[MinValueValidator(Decimal('0.00'))],
#         verbose_name="Próba 1 [kg]"
#     )
#     attempt2_weight = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         validators=[MinValueValidator(Decimal('0.00'))],
#         verbose_name="Próba 2 [kg]"
#     )
#     attempt3_weight = models.DecimalField(
#         max_digits=5,
#         decimal_places=2,
#         default=Decimal('0.00'),
#         validators=[MinValueValidator(Decimal('0.00'))],
#         verbose_name="Próba 3 [kg]"
#     )
#
#     # === Metadane ===
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return f"{self.athlete} - {self.exercise_type} ({self.category})"
#
#     class Meta:
#         verbose_name = "Ćwiczenie"
#         verbose_name_plural = "Ćwiczenia"
#         unique_together = [['athlete', 'exercise_type', 'category']]
#
#     # === Metody pomocnicze ===
#
#     def _get_best_attempt(self):
#         """Zwraca najlepszą próbę z trzech."""
#         return max(self.attempt1_weight, self.attempt2_weight, self.attempt3_weight)
#
#     # === Metody obliczania wyników ===
#
#     def calculate_score(self):
#         """
#         Oblicza wynik ćwiczenia na podstawie metody kalkulacji określonej w typie ćwiczenia.
#         """
#         calculation_method = self.exercise_type.calculation_method
#
#         if calculation_method == 'weight_x_reps':
#             # Dla Snatch: waga odważnika × liczba powtórzeń
#             return float(self.kettlebell_weight) * self.repetitions
#
#         elif calculation_method == 'weight_to_body':
#             # Dla ćwiczeń o stosunku do masy ciała (TGU, Press)
#             best_attempt = float(self._get_best_attempt())
#             body_weight = float(self.athlete.body_weight)
#
#             if best_attempt > 0 and body_weight > 0:
#                 return best_attempt / body_weight
#             return 0
#
#         elif calculation_method == 'best_attempt':
#             # Zwraca po prostu najlepszą próbę
#             return float(self._get_best_attempt())
#
#         # Możliwość rozszerzenia o inne metody kalkulacji
#         return 0
#
#     # === Metody aktualizacji ===
#
#     def update_snatch(self, weight, repetitions):
#         """Aktualizuje wyniki Snatch."""
#         self.kettlebell_weight = Decimal(str(weight))
#         self.repetitions = repetitions
#         self.save(update_fields=['kettlebell_weight', 'repetitions'])
#         return self
#
#     def update_attempt(self, attempt_number, weight):
#         """Aktualizuje wybraną próbę."""
#         if attempt_number not in (1, 2, 3):
#             raise ValueError("Numer próby musi być 1, 2 lub 3.")
#
#         field_name = f"attempt{attempt_number}_weight"
#         setattr(self, field_name, Decimal(str(weight)))
#         self.save(update_fields=[field_name])
#         return self

# -*- coding: utf-8 -*-
"""Model definition for Player."""
from typing import Optional, TYPE_CHECKING
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

# Zapobieganie błędom importu kołowego przy type hinting
if TYPE_CHECKING:
    from .category import Category
    from .sport_club import SportClub
    from .results.snatch import SnatchResult
    from .results.tgu import TGUResult
    from .results.pistol_squat import PistolSquatResult
    from .results.see_saw_press import SeeSawPressResult, BestSeeSawPressResult
    from .results.kb_squat import KBSquatResult, BestKBSquatResult
    from .results.overall import OverallResult

class Player(models.Model):
    """Represents a competitor."""
    name = models.CharField(_("Imię"), max_length=50)
    surname = models.CharField(_("Nazwisko"), max_length=50)
    weight = models.FloatField(_("Waga (kg)"), null=True, blank=True, default=0.0) # Lepszy label, default float
    club = models.ForeignKey[Optional['Klub']](
        'SportClub', # Użycie stringa zapobiega importom kołowym na starcie
        on_delete=models.SET_NULL, # Lepsze niż CASCADE? Co jeśli klub zniknie?
        null=True,
        blank=True, # Czy klub jest wymagany? Jeśli tak, usuń null=True, blank=True
        verbose_name=_("Sport Club"),
        related_name="players"
    )
    categories = models.ManyToManyField(
        'Category', # Użycie stringa
        verbose_name=_("Categories"),
        related_name="players",
        blank=True # Czy zawodnik musi mieć kategorię?
    )
    tiebreak = models.BooleanField(_("Tiebreak applied"), default=False)

    # --- Pola do wprowadzania wyników (rozważ przeniesienie do dedykowanych modeli lub formularzy) ---
    # Te pola wydają się nadmiarowe, skoro mamy dedykowane modele wyników.
    # Prawdopodobnie powinny być usuwane, a wyniki wprowadzane bezpośrednio
    # przez admina do modeli wyników lub przez dedykowany interfejs.
    # Zostawiam je na razie, jak w oryginale, ale to główny kandydat do refaktoryzacji.

    # Snatch Input Fields
    snatch_kettlebell_weight = models.FloatField(_("Snatch: Waga Kettlebell"), null=True, blank=True, default=0.0)
    snatch_repetitions = models.IntegerField(_("Snatch: Ilość Powtórzeń"), null=True, blank=True, default=0)

    # TGU Input Fields
    tgu_weight_1 = models.FloatField(_("TGU: Próba I"), null=True, blank=True, default=0.0)
    tgu_weight_2 = models.FloatField(_("TGU: Próba II"), null=True, blank=True, default=0.0)
    tgu_weight_3 = models.FloatField(_("TGU: Próba III"), null=True, blank=True, default=0.0)

    # See Saw Press Input Fields
    see_saw_press_weight_left_1 = models.FloatField(_("SSP Próba I L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_2 = models.FloatField(_("SSP Próba II L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_3 = models.FloatField(_("SSP Próba III L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_1 = models.FloatField(_("SSP Próba I R"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_2 = models.FloatField(_("SSP Próba II R"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_3 = models.FloatField(_("SSP Próba III R"), null=True, blank=True, default=0.0)

    # KB Squat Input Fields
    kb_squat_weight_left_1 = models.FloatField(_("Kettlebell Squat: Próba I L"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_2 = models.FloatField(_("Kettlebell Squat: Próba II L"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_3 = models.FloatField(_("Kettlebell Squat: Próba III L"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_1 = models.FloatField(_("Kettlebell Squat: Próba I R"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_2 = models.FloatField(_("Kettlebell Squat: Próba II R"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_3 = models.FloatField(_("Kettlebell Squat: Próba III R"), null=True, blank=True, default=0.0)

    # Pistol Squat Input Fields
    pistol_squat_weight_1 = models.FloatField(_("Pistol Squat: Próba I"), null=True, blank=True, default=0.0)
    pistol_squat_weight_2 = models.FloatField(_("Pistol Squat: Próba II"), null=True, blank=True, default=0.0)
    pistol_squat_weight_3 = models.FloatField(_("Pistol Squat: Próba III"), null=True, blank=True, default=0.0)

    # One Kettlebell Press Input Fields
    one_kb_press_weight_1 = models.FloatField(_("One Kettllebell Press: Próba I"), null=True, blank=True, default=0.0)
    one_kb_press_weight_2 = models.FloatField(_("One Kettllebell Press: Próba II"), null=True, blank=True, default=0.0)
    one_kb_press_weight_3 = models.FloatField(_("One Kettllebell Press: Próba III"), null=True, blank=True, default=0.0)

    # Two Kettlebell Press Input Fields
    two_kb_press_weight_left_1 = models.FloatField(_("Two Kettlebell Press: Próba I L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_1 = models.FloatField(_("Two Kettlebell Press: Próba I R"), null=True, blank=True, default=0.0)
    two_kb_press_weight_left_2 = models.FloatField(_("Two Kettlebell Press: Próba II L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_2 = models.FloatField(_("Two Kettlebell Press: Próba II R"), null=True, blank=True, default=0.0)
    two_kb_press_weight_left_3 = models.FloatField(_("Two Kettlebell Press: Próba III L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_3 = models.FloatField(_("Two Kettlebell Press: Próba III R"), null=True, blank=True, default=0.0)
    # --- Koniec pól do wprowadzania ---

    _updating_results: bool = False # Flaga zapobiegająca rekursji w save()

    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["surname", "name"]
        unique_together = [('name', 'surname', 'club')] # Czy zawodnik jest unikalny w ramach klubu?

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    @property
    def full_name(self) -> str:
        """Returns the player's full name."""
        return f"{self.name} {self.surname}"

    # --- Metody aktualizujące powiązane wyniki ---
    # Te metody powinny być prawdopodobnie wywoływane przez sygnały post_save
    # lub dedykowaną logikę serwisową po zapisaniu pól wejściowych,
    # zamiast bezpośrednio w save() Player.

    @transaction.atomic
    def update_related_results(self) -> None:
        """
        Updates all related result models based on the current Player instance's
        input fields.
        """
        if self._updating_results:
            return
        self._updating_results = True

        # Importuj modele tutaj, aby uniknąć problemów z importem kołowym
        from .results.snatch import SnatchResult
        from .results.tgu import TGUResult
        from .results.pistol_squat import PistolSquatResult
        from .results.see_saw_press import SeeSawPressResult, BestSeeSawPressResult
        from .results.kb_squat import KBSquatResult, BestKBSquatResult
        from .results.one_kettlebell_press import OneKettlebellPressResult  # <--- NOWY IMPORT
        from .results.two_kettlebell_press import TwoKettlebellPressResult, \
            BestTwoKettlebellPressResult  # <--- NOWE IMPORTY
        from .services import update_overall_results_for_player

        try:
            # ... (aktualizacje dla Snatch, TGU, Pistol, SSP, KBS - bez zmian) ...

            # Update Kettlebell Press Wyniki
            okbp_result, _ = OneKettlebellPressResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_1': self.one_kb_press_weight_1 or 0.0,
                    'result_2': self.one_kb_press_weight_2 or 0.0,
                    'result_3': self.one_kb_press_weight_3 or 0.0,
                }
            )

            # Update Two Kettlebell Press Result
            tkbp_result, _ = TwoKettlebellPressResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_left_1': self.two_kb_press_weight_left_1 or 0.0,
                    'result_right_1': self.two_kb_press_weight_right_1 or 0.0,
                    'result_left_2': self.two_kb_press_weight_left_2 or 0.0,
                    'result_right_2': self.two_kb_press_weight_right_2 or 0.0,
                    'result_left_3': self.two_kb_press_weight_left_3 or 0.0,
                    'result_right_3': self.two_kb_press_weight_right_3 or 0.0,
                }
            )
            # Update Best Two Kettlebell Press Result
            best_tkbp, _ = BestTwoKettlebellPressResult.objects.get_or_create(player=self)
            best_tkbp.update_best_result()  # Metoda na modelu Best...

            # Update Overall Results (triggered after all individual results are saved)
            update_overall_results_for_player(self)

        finally:
            self._updating_results = False

    def save(self, *args, **kwargs) -> None:
        """Overrides save to trigger updates of related result models."""
        super().save(*args, **kwargs)
        # Wywołanie aktualizacji po zapisie - rozważ sygnały post_save
        self.update_related_results()

    # --- Metody obliczeniowe (properties mogą być lepsze) ---

    def calculate_snatch_score(self) -> Optional[float]:
        """Calculates the snatch score (weight * reps)."""
        if self.snatch_kettlebell_weight is not None and self.snatch_repetitions is not None:
            return round(self.snatch_kettlebell_weight * self.snatch_repetitions, 1)
        return None

    def get_max_tgu_weight(self) -> float:
        """Returns the maximum weight lifted in TGU across all attempts."""
        return max(self.tgu_weight_1 or 0.0, self.tgu_weight_2 or 0.0, self.tgu_weight_3 or 0.0)

    def get_max_pistol_squat_weight(self) -> float:
        """Returns the maximum weight lifted in Pistol Squat across all attempts."""
        return max(
            self.pistol_squat_weight_1 or 0.0,
            self.pistol_squat_weight_2 or 0.0,
            self.pistol_squat_weight_3 or 0.0,
        )

    # Metody xxx_body_percent_weight() zostały przeniesione do odpowiednich modeli wyników,
    # gdzie mają dostęp do wyniku i wagi zawodnika.
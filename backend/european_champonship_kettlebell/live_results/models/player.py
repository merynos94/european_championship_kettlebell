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
    name = models.CharField(_("Name"), max_length=50)
    surname = models.CharField(_("Surname"), max_length=50)
    weight = models.FloatField(_("Weight (kg)"), null=True, blank=True, default=0.0) # Lepszy label, default float
    club = models.ForeignKey[Optional['SportClub']](
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
    snatch_kettlebell_weight = models.FloatField(_("Snatch: KB Weight"), null=True, blank=True, default=0.0)
    snatch_repetitions = models.IntegerField(_("Snatch: Repetitions"), null=True, blank=True, default=0)

    # TGU Input Fields
    tgu_weight_1 = models.FloatField(_("TGU: Attempt 1 Weight"), null=True, blank=True, default=0.0)
    tgu_weight_2 = models.FloatField(_("TGU: Attempt 2 Weight"), null=True, blank=True, default=0.0)
    tgu_weight_3 = models.FloatField(_("TGU: Attempt 3 Weight"), null=True, blank=True, default=0.0)

    # See Saw Press Input Fields
    see_saw_press_weight_left_1 = models.FloatField(_("SSP Left: Attempt 1"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_2 = models.FloatField(_("SSP Left: Attempt 2"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_3 = models.FloatField(_("SSP Left: Attempt 3"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_1 = models.FloatField(_("SSP Right: Attempt 1"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_2 = models.FloatField(_("SSP Right: Attempt 2"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_3 = models.FloatField(_("SSP Right: Attempt 3"), null=True, blank=True, default=0.0)

    # KB Squat Input Fields
    kb_squat_weight_left_1 = models.FloatField(_("KBS Left: Attempt 1"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_2 = models.FloatField(_("KBS Left: Attempt 2"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_3 = models.FloatField(_("KBS Left: Attempt 3"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_1 = models.FloatField(_("KBS Right: Attempt 1"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_2 = models.FloatField(_("KBS Right: Attempt 2"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_3 = models.FloatField(_("KBS Right: Attempt 3"), null=True, blank=True, default=0.0)

    # Pistol Squat Input Fields
    pistol_squat_weight_1 = models.FloatField(_("Pistol: Attempt 1"), null=True, blank=True, default=0.0)
    pistol_squat_weight_2 = models.FloatField(_("Pistol: Attempt 2"), null=True, blank=True, default=0.0)
    pistol_squat_weight_3 = models.FloatField(_("Pistol: Attempt 3"), null=True, blank=True, default=0.0)
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
        input fields. This is likely triggered after saving the Player model.
        Consider moving this logic to signals or a service layer.
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
        from .services import update_overall_results_for_player # Zaimportuj funkcję serwisową

        try:
            # Update Snatch Result
            snatch_result, _ = SnatchResult.objects.update_or_create(
                player=self,
                defaults={'result': self.calculate_snatch_score()}
            )

            # Update TGU Result
            tgu_result, _ = TGUResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_1': self.tgu_weight_1 or 0.0,
                    'result_2': self.tgu_weight_2 or 0.0,
                    'result_3': self.tgu_weight_3 or 0.0,
                }
            )

            # Update Pistol Squat Result
            pistol_result, _ = PistolSquatResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_1': self.pistol_squat_weight_1 or 0.0,
                    'result_2': self.pistol_squat_weight_2 or 0.0,
                    'result_3': self.pistol_squat_weight_3 or 0.0,
                }
            )

            # Update See Saw Press Result
            ssp_result, _ = SeeSawPressResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_left_1': self.see_saw_press_weight_left_1 or 0.0,
                    'result_right_1': self.see_saw_press_weight_right_1 or 0.0,
                    'result_left_2': self.see_saw_press_weight_left_2 or 0.0,
                    'result_right_2': self.see_saw_press_weight_right_2 or 0.0,
                    'result_left_3': self.see_saw_press_weight_left_3 or 0.0,
                    'result_right_3': self.see_saw_press_weight_right_3 or 0.0,
                }
            )
            # Update Best See Saw Press Result
            best_ssp, _ = BestSeeSawPressResult.objects.get_or_create(player=self)
            best_ssp.update_best_results() # Metoda na modelu Best...

            # Update KB Squat Result
            kbs_result, _ = KBSquatResult.objects.update_or_create(
                player=self,
                defaults={
                    'result_left_1': self.kb_squat_weight_left_1 or 0.0,
                    'result_right_1': self.kb_squat_weight_right_1 or 0.0,
                    'result_left_2': self.kb_squat_weight_left_2 or 0.0,
                    'result_right_2': self.kb_squat_weight_right_2 or 0.0,
                    'result_left_3': self.kb_squat_weight_left_3 or 0.0,
                    'result_right_3': self.kb_squat_weight_right_3 or 0.0,
                }
            )
            # Update Best KB Squat Result
            best_kbs, _ = BestKBSquatResult.objects.get_or_create(player=self)
            best_kbs.update_best_result() # Metoda na modelu Best...

            # Update Overall Results (consider if this should be triggered elsewhere)
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
"""Model definition for Player."""

from typing import TYPE_CHECKING, Optional

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass


class Player(models.Model):
    """Represents a competitor."""

    name = models.CharField(_("Imię"), max_length=50)
    surname = models.CharField(_("Nazwisko"), max_length=50)
    weight = models.FloatField(_("Waga (kg)"), null=True, blank=True, default=0.0)  # Lepszy label, default float
    club = models.ForeignKey[Optional["Klub"]](
        "SportClub",  # Użycie stringa zapobiega importom kołowym na starcie
        on_delete=models.SET_NULL,  # Lepsze niż CASCADE? Co jeśli klub zniknie?
        null=True,
        blank=True,  # Czy klub jest wymagany? Jeśli tak, usuń null=True, blank=True
        verbose_name=_("Klub"),
        related_name="players",
    )
    categories = models.ManyToManyField(
        "Category",  # Użycie stringa
        verbose_name=_("Categories"),
        related_name="players",
        blank=True,  # Czy zawodnik musi mieć kategorię?
    )
    tiebreak = models.BooleanField(_("Tiebreak applied"), default=False)

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
    two_kb_press_weight_left_1 = models.FloatField(
        _("Two Kettlebell Press: Próba I L"), null=True, blank=True, default=0.0
    )
    two_kb_press_weight_right_1 = models.FloatField(
        _("Two Kettlebell Press: Próba I R"), null=True, blank=True, default=0.0
    )
    two_kb_press_weight_left_2 = models.FloatField(
        _("Two Kettlebell Press: Próba II L"), null=True, blank=True, default=0.0
    )
    two_kb_press_weight_right_2 = models.FloatField(
        _("Two Kettlebell Press: Próba II R"), null=True, blank=True, default=0.0
    )
    two_kb_press_weight_left_3 = models.FloatField(
        _("Two Kettlebell Press: Próba III L"), null=True, blank=True, default=0.0
    )
    two_kb_press_weight_right_3 = models.FloatField(
        _("Two Kettlebell Press: Próba III R"), null=True, blank=True, default=0.0
    )
    # --- Koniec pól do wprowadzania ---

    _updating_results: bool = False  # Flaga zapobiegająca rekursji w save()

    class Meta:
        verbose_name = _("Zawodnik")
        verbose_name_plural = _("Zawodnicy")
        ordering = ["surname", "name"]
        unique_together = [("name", "surname", "club")]  # Czy zawodnik jest unikalny w ramach klubu?

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    @property
    def full_name(self) -> str:
        """Returns the player's full name."""
        return f"{self.name} {self.surname}"

        # Wewnątrz klasy Player w pliku player.py

    @transaction.atomic
    def update_related_results(self) -> None:
        """
        Aktualizuje wszystkie powiązane modele wyników (surowych i najlepszych)
        na podstawie pól wprowadzonych w bieżącej instancji Player.
        ZAWIERA DODATKOWE WYDRUKI DEBUGOWE.
        """
        # Flaga zapobiegająca rekursji
        if getattr(self, "_updating_results", False):
            print(f"DEBUG Player {self.id}: update_related_results - Wykryto rekurencję, pomijam.")
            return
        self._updating_results = True
        print(f"==== DEBUG Player {self.id} ({self}): Rozpoczynam update_related_results ====")

        # --- Importuj modele wewnątrz metody ---
        # Upewnij się, że wszystkie te importy są poprawne dla Twojej struktury!
        print(f"DEBUG Player {self.id}: Importuję modele wyników...")
        try:
            from .results.kb_squat import BestKBSquatResult, KBSquatResult
            from .results.one_kettlebell_press import (
                BestOneKettlebellPressResult,  # UPEWNIJ SIĘ, ŻE JEST!
                OneKettlebellPressResult,
            )
            from .results.pistol_squat import BestPistolSquatResult, PistolSquatResult
            from .results.see_saw_press import BestSeeSawPressResult, SeeSawPressResult
            from .results.snatch import BestSnatchResult, SnatchResult
            from .results.tgu import BestTGUResult, TGUResult
            from .results.two_kettlebell_press import BestTwoKettlebellPressResult, TwoKettlebellPressResult
            from .services import update_overall_results_for_player

            print(f"DEBUG Player {self.id}: Importy modeli zakończone sukcesem.")
        except ImportError as e:
            print(f"!!!!!!!!! BŁĄD KRYTYCZNY Player {self.id}: Błąd importu w update_related_results: {e} !!!!!!!!!")
            self._updating_results = False
            return  # Przerwij, jeśli import się nie udał

        try:
            print(f"\n--- DEBUG Player {self.id}: Przetwarzam Snatch ---")
            snatch_score = None
            if self.snatch_kettlebell_weight is not None and self.snatch_repetitions is not None:
                weight = self.snatch_kettlebell_weight or 0.0
                reps = self.snatch_repetitions or 0
                snatch_score = round(weight * reps, 1) if weight > 0 and reps > 0 else None
            print(f"DEBUG Snatch: Obliczony snatch_score: {snatch_score}")
            snatch_result_obj, created_raw = SnatchResult.objects.update_or_create(
                player=self, defaults={"result": snatch_score}
            )
            print(f"DEBUG Snatch: update_or_create raw: created={created_raw}, result={snatch_result_obj.result}")
            best_snatch_obj, created_best = BestSnatchResult.objects.get_or_create(player=self)
            print(
                f"DEBUG Snatch: get_or_create best: created={created_best}, current_best_result={best_snatch_obj.best_result}"
            )
            updated_snatch = best_snatch_obj.update_best_result()
            print(
                f"DEBUG Snatch: update_best_result zwróciło: {updated_snatch}, new_best_result={best_snatch_obj.best_result}"
            )

            print(f"\n--- DEBUG Player {self.id}: Przetwarzam TGU ---")
            print(f"DEBUG TGU: Wartości wejściowe: {self.tgu_weight_1}, {self.tgu_weight_2}, {self.tgu_weight_3}")
            tgu_result_obj, created_raw = TGUResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_1": self.tgu_weight_1 or 0.0,
                    "result_2": self.tgu_weight_2 or 0.0,
                    "result_3": self.tgu_weight_3 or 0.0,
                },
            )
            print(f"DEBUG TGU: update_or_create raw: created={created_raw}, max_result={tgu_result_obj.max_result}")
            best_tgu_obj, created_best = BestTGUResult.objects.get_or_create(player=self)
            print(
                f"DEBUG TGU: get_or_create best: created={created_best}, current_best_result={best_tgu_obj.best_result}"
            )
            updated_tgu = best_tgu_obj.update_best_result()
            print(f"DEBUG TGU: update_best_result zwróciło: {updated_tgu}, new_best_result={best_tgu_obj.best_result}")

            print(f"\n--- DEBUG Player {self.id}: Przetwarzam Pistol Squat ---")
            print(
                f"DEBUG Pistol: Wartości wejściowe: {self.pistol_squat_weight_1}, {self.pistol_squat_weight_2}, {self.pistol_squat_weight_3}"
            )
            pistol_result_obj, created_raw = PistolSquatResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_1": self.pistol_squat_weight_1 or 0.0,
                    "result_2": self.pistol_squat_weight_2 or 0.0,
                    "result_3": self.pistol_squat_weight_3 or 0.0,
                },
            )
            print(
                f"DEBUG Pistol: update_or_create raw: created={created_raw}, max_result={pistol_result_obj.max_result}"
            )
            best_pistol_obj, created_best = BestPistolSquatResult.objects.get_or_create(player=self)
            print(
                f"DEBUG Pistol: get_or_create best: created={created_best}, current_best_result={best_pistol_obj.best_result}"
            )
            updated_pistol = best_pistol_obj.update_best_result()
            print(
                f"DEBUG Pistol: update_best_result zwróciło: {updated_pistol}, new_best_result={best_pistol_obj.best_result}"
            )

            print(f"\n--- DEBUG Player {self.id}: Przetwarzam See Saw Press ---")
            print(
                f"DEBUG SSP: Wartości wejściowe L: {self.see_saw_press_weight_left_1}, {self.see_saw_press_weight_left_2}, {self.see_saw_press_weight_left_3}"
            )
            print(
                f"DEBUG SSP: Wartości wejściowe R: {self.see_saw_press_weight_right_1}, {self.see_saw_press_weight_right_2}, {self.see_saw_press_weight_right_3}"
            )
            ssp_result_obj, created_raw = SeeSawPressResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_left_1": self.see_saw_press_weight_left_1 or 0.0,
                    "result_right_1": self.see_saw_press_weight_right_1 or 0.0,
                    "result_left_2": self.see_saw_press_weight_left_2 or 0.0,
                    "result_right_2": self.see_saw_press_weight_right_2 or 0.0,
                    "result_left_3": self.see_saw_press_weight_left_3 or 0.0,
                    "result_right_3": self.see_saw_press_weight_right_3 or 0.0,
                },
            )
            print(
                f"DEBUG SSP: update_or_create raw: created={created_raw}, max_score={getattr(ssp_result_obj, 'max_score', 'N/A')}"
            )  # Użyj getattr, bo max_score to property
            best_ssp_obj, created_best = BestSeeSawPressResult.objects.get_or_create(player=self)
            print(
                f"DEBUG SSP: get_or_create best: created={created_best}, current_best_result L/R={best_ssp_obj.best_left}/{best_ssp_obj.best_right}"
            )
            updated_ssp = best_ssp_obj.update_best_result()
            print(
                f"DEBUG SSP: update_best_result zwróciło: {updated_ssp}, new_best_result L/R={best_ssp_obj.best_left}/{best_ssp_obj.best_right}"
            )

            print(f"\n--- DEBUG Player {self.id}: Przetwarzam KB Squat ---")
            print(
                f"DEBUG KBS: Wartości wejściowe L: {self.kb_squat_weight_left_1}, {self.kb_squat_weight_left_2}, {self.kb_squat_weight_left_3}"
            )
            print(
                f"DEBUG KBS: Wartości wejściowe R: {self.kb_squat_weight_right_1}, {self.kb_squat_weight_right_2}, {self.kb_squat_weight_right_3}"
            )
            kbs_result_obj, created_raw = KBSquatResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_left_1": self.kb_squat_weight_left_1 or 0.0,
                    "result_right_1": self.kb_squat_weight_right_1 or 0.0,
                    "result_left_2": self.kb_squat_weight_left_2 or 0.0,
                    "result_right_2": self.kb_squat_weight_right_2 or 0.0,
                    "result_left_3": self.kb_squat_weight_left_3 or 0.0,
                    "result_right_3": self.kb_squat_weight_right_3 or 0.0,
                },
            )
            print(
                f"DEBUG KBS: update_or_create raw: created={created_raw}, max_score={getattr(kbs_result_obj, 'max_score', 'N/A')}"
            )
            best_kbs_obj, created_best = BestKBSquatResult.objects.get_or_create(player=self)
            print(
                f"DEBUG KBS: get_or_create best: created={created_best}, current_best_result={best_kbs_obj.best_result}"
            )
            updated_kbs = best_kbs_obj.update_best_result()
            print(f"DEBUG KBS: update_best_result zwróciło: {updated_kbs}, new_best_result={best_kbs_obj.best_result}")

            # ----> BLOK DO OBSERWACJI <----
            print(f"\n--- DEBUG Player {self.id}: Przetwarzam One Kettlebell Press ---")
            print(
                f"DEBUG OKBP: Wartości wejściowe: {self.one_kb_press_weight_1}, {self.one_kb_press_weight_2}, {self.one_kb_press_weight_3}"
            )
            okbp_result_obj, created_raw = OneKettlebellPressResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_1": self.one_kb_press_weight_1 or 0.0,
                    "result_2": self.one_kb_press_weight_2 or 0.0,
                    "result_3": self.one_kb_press_weight_3 or 0.0,
                },
            )
            print(f"DEBUG OKBP: update_or_create raw: created={created_raw}, max_result={okbp_result_obj.max_result}")
            print("DEBUG OKBP: Próbuję get_or_create BestOneKettlebellPressResult...")
            best_okbp_obj, created_best = BestOneKettlebellPressResult.objects.get_or_create(
                player=self
            )  # Czy tu wystąpi błąd NameError?
            print(
                f"DEBUG OKBP: get_or_create best: created={created_best}, current_best_result={best_okbp_obj.best_result}"
            )
            print("DEBUG OKBP: Wywołuję update_best_result dla Best OKBP...")
            # Dodajmy też print wewnątrz metody update_best_result w BestOneKettlebellPressResult, jak sugerowałem wcześniej
            updated_okbp = best_okbp_obj.update_best_result()
            print(f"DEBUG OKBP: update_best_result zwróciło: {updated_okbp}")
            print(f"DEBUG OKBP: Zapisany best_result w Best OKBP: {best_okbp_obj.best_result}")
            print("--- DEBUG: Zakończono OKBP ---")
            # ----> KONIEC BLOKU DO OBSERWACJI <----

            print(f"\n--- DEBUG Player {self.id}: Przetwarzam Two Kettlebell Press ---")
            print(
                f"DEBUG TKBP: Wartości wejściowe L: {self.two_kb_press_weight_left_1}, {self.two_kb_press_weight_left_2}, {self.two_kb_press_weight_left_3}"
            )
            print(
                f"DEBUG TKBP: Wartości wejściowe R: {self.two_kb_press_weight_right_1}, {self.two_kb_press_weight_right_2}, {self.two_kb_press_weight_right_3}"
            )
            tkbp_result_obj, created_raw = TwoKettlebellPressResult.objects.update_or_create(
                player=self,
                defaults={
                    "result_left_1": self.two_kb_press_weight_left_1 or 0.0,
                    "result_right_1": self.two_kb_press_weight_right_1 or 0.0,
                    "result_left_2": self.two_kb_press_weight_left_2 or 0.0,
                    "result_right_2": self.two_kb_press_weight_right_2 or 0.0,
                    "result_left_3": self.two_kb_press_weight_left_3 or 0.0,
                    "result_right_3": self.two_kb_press_weight_right_3 or 0.0,
                },
            )
            print(
                f"DEBUG TKBP: update_or_create raw: created={created_raw}, max_score={getattr(tkbp_result_obj, 'max_score', 'N/A')}"
            )
            best_tkbp_obj, created_best = BestTwoKettlebellPressResult.objects.get_or_create(player=self)
            print(
                f"DEBUG TKBP: get_or_create best: created={created_best}, current_best_result={best_tkbp_obj.best_result}"
            )
            updated_tkbp = best_tkbp_obj.update_best_result()
            print(
                f"DEBUG TKBP: update_best_result zwróciło: {updated_tkbp}, new_best_result={best_tkbp_obj.best_result}"
            )

            # --- Na koniec zaktualizuj wyniki ogólne ---
            print(f"\n--- DEBUG Player {self.id}: Wywołuję update_overall_results_for_player ---")
            update_overall_results_for_player(self)
            print(f"--- DEBUG Player {self.id}: Zakończono update_overall_results_for_player ---")

        except Exception as e:
            # Logowanie błędów jest BARDZO WAŻNE
            print(f"!!!!!!!!!! BŁĄD Player {self.id} w GŁÓWNYM TRY update_related_results: {e} !!!!!!!!!!!")
            import traceback

            traceback.print_exc()  # Wydrukuj pełny traceback błędu
        finally:
            # Zawsze zwalniaj flagę
            print(f"==== DEBUG Player {self.id}: Kończę update_related_results (finally) ====")
            self._updating_results = False

    def save(self, *args, **kwargs) -> None:
        """Nadpisuje save, aby wywołać aktualizację powiązanych wyników."""
        print(f"==== Player {self.id if self.pk else 'NEW'} ({self}): !!! WYWOŁANO METODĘ Player.save() !!! ====")

        # Najpierw wykonaj standardowy zapis obiektu Player
        super().save(*args, **kwargs)
        print(f"==== Player {self.id}: super().save() zakończone.")

        # Następnie wywołaj aktualizację wyników
        print(f"==== Player {self.id}: Wywołuję self.update_related_results() z metody save()... ====")
        try:
            self.update_related_results()
            print(f"==== Player {self.id}: self.update_related_results() zakończone.")
        except Exception as e_update:
            print(
                f"!!!!!!!!! Player {self.id}: BŁĄD podczas wywołania update_related_results() z save(): {e_update} !!!!!!!!!"
            )
            import traceback

            traceback.print_exc()

        print(f"==== Player {self.id}: Zakończono metodę Player.save() ====")

    def calculate_snatch_score(self) -> float | None:
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

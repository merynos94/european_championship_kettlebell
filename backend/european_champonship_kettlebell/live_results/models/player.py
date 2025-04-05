# player.py
"""Model definition for Player."""

from typing import TYPE_CHECKING, Optional

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from .category import Category
    from .results.overall import OverallResult
    from .results.snatch import SnatchResult, BestSnatchResult # BestSnatch pozostaje
    from .results.tgu import TGUResult
    from .results.pistol_squat import PistolSquatResult
    from .results.see_saw_press import SeeSawPressResult # Usunięto Best...
    from .results.kb_squat import KBSquatResult # Usunięto Best...
    from .results.one_kettlebell_press import OneKettlebellPressResult
    from .results.two_kettlebell_press import TwoKettlebellPressResult # Usunięto Best...
    from .sport_club import SportClub


class Player(models.Model):
    """Represents a competitor."""

    name = models.CharField(_("Imię"), max_length=50)
    surname = models.CharField(_("Nazwisko"), max_length=50)
    weight = models.FloatField(_("Waga (kg)"), null=True, blank=True, default=0.0)
    club = models.ForeignKey[Optional["SportClub"]](
        "SportClub", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Klub"), related_name="players"
    )
    categories = models.ManyToManyField(
        "Category", verbose_name=_("Categories"), related_name="players", blank=True
    )
    tiebreak = models.BooleanField(_("Tiebreak applied"), default=False)

    # --- Input Fields (bez zmian) ---
    snatch_kettlebell_weight = models.FloatField(_("Snatch: Waga Kettlebell"), null=True, blank=True, default=0.0)
    snatch_repetitions = models.IntegerField(_("Snatch: Ilość Powtórzeń"), null=True, blank=True, default=0)
    tgu_weight_1 = models.FloatField(_("TGU: Próba I"), null=True, blank=True, default=0.0)
    tgu_weight_2 = models.FloatField(_("TGU: Próba II"), null=True, blank=True, default=0.0)
    tgu_weight_3 = models.FloatField(_("TGU: Próba III"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_1 = models.FloatField(_("SSP Próba I L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_2 = models.FloatField(_("SSP Próba II L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_left_3 = models.FloatField(_("SSP Próba III L"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_1 = models.FloatField(_("SSP Próba I R"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_2 = models.FloatField(_("SSP Próba II R"), null=True, blank=True, default=0.0)
    see_saw_press_weight_right_3 = models.FloatField(_("SSP Próba III R"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_1 = models.FloatField(_("Kettlebell Squat: Próba I L"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_2 = models.FloatField(_("Kettlebell Squat: Próba II L"), null=True, blank=True, default=0.0)
    kb_squat_weight_left_3 = models.FloatField(_("Kettlebell Squat: Próba III L"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_1 = models.FloatField(_("Kettlebell Squat: Próba I R"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_2 = models.FloatField(_("Kettlebell Squat: Próba II R"), null=True, blank=True, default=0.0)
    kb_squat_weight_right_3 = models.FloatField(_("Kettlebell Squat: Próba III R"), null=True, blank=True, default=0.0)
    pistol_squat_weight_1 = models.FloatField(_("Pistol Squat: Próba I"), null=True, blank=True, default=0.0)
    pistol_squat_weight_2 = models.FloatField(_("Pistol Squat: Próba II"), null=True, blank=True, default=0.0)
    pistol_squat_weight_3 = models.FloatField(_("Pistol Squat: Próba III"), null=True, blank=True, default=0.0)
    one_kb_press_weight_1 = models.FloatField(_("One Kettllebell Press: Próba I"), null=True, blank=True, default=0.0)
    one_kb_press_weight_2 = models.FloatField(_("One Kettllebell Press: Próba II"), null=True, blank=True, default=0.0)
    one_kb_press_weight_3 = models.FloatField(_("One Kettllebell Press: Próba III"), null=True, blank=True, default=0.0)
    two_kb_press_weight_left_1 = models.FloatField(_("Two Kettlebell Press: Próba I L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_1 = models.FloatField(_("Two Kettlebell Press: Próba I R"), null=True, blank=True, default=0.0)
    two_kb_press_weight_left_2 = models.FloatField(_("Two Kettlebell Press: Próba II L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_2 = models.FloatField(_("Two Kettlebell Press: Próba II R"), null=True, blank=True, default=0.0)
    two_kb_press_weight_left_3 = models.FloatField(_("Two Kettlebell Press: Próba III L"), null=True, blank=True, default=0.0)
    two_kb_press_weight_right_3 = models.FloatField(_("Two Kettlebell Press: Próba III R"), null=True, blank=True, default=0.0)
    # --- End Input Fields ---

    _updating_results: bool = False

    class Meta:
        verbose_name = _("Zawodnik")
        verbose_name_plural = _("Zawodnicy")
        ordering = ["surname", "name"]

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"

    @transaction.atomic
    def update_related_results(self) -> None:
        if getattr(self, "_updating_results", False): return
        self._updating_results = True
        try:
            # Importy
            from .results.kb_squat import KBSquatResult
            from .results.one_kettlebell_press import OneKettlebellPressResult
            from .results.pistol_squat import PistolSquatResult
            from .results.see_saw_press import SeeSawPressResult
            from .results.snatch import SnatchResult, BestSnatchResult
            from .results.tgu import TGUResult
            from .results.two_kettlebell_press import TwoKettlebellPressResult
            from .services import update_overall_results_for_player

            # --- Snatch ---
            snatch_score = self.calculate_snatch_score()
            SnatchResult.objects.update_or_create(player=self, defaults={"result": snatch_score})
            try:
                best_snatch_obj, _ = BestSnatchResult.objects.get_or_create(player=self)
                best_snatch_obj.update_best_result()
            except Exception as e: print(f"BŁĄD aktualizacji BestSnatch dla {self}: {e}")

            # --- TGU ---
            TGUResult.objects.update_or_create(player=self, defaults={"result_1": self.tgu_weight_1 or 0.0, "result_2": self.tgu_weight_2 or 0.0, "result_3": self.tgu_weight_3 or 0.0})

            # --- Pistol Squat ---
            PistolSquatResult.objects.update_or_create(player=self, defaults={"result_1": self.pistol_squat_weight_1 or 0.0, "result_2": self.pistol_squat_weight_2 or 0.0, "result_3": self.pistol_squat_weight_3 or 0.0})

            # --- See Saw Press ---
            SeeSawPressResult.objects.update_or_create(player=self, defaults={"result_left_1": self.see_saw_press_weight_left_1 or 0.0, "result_right_1": self.see_saw_press_weight_right_1 or 0.0, "result_left_2": self.see_saw_press_weight_left_2 or 0.0, "result_right_2": self.see_saw_press_weight_right_2 or 0.0, "result_left_3": self.see_saw_press_weight_left_3 or 0.0, "result_right_3": self.see_saw_press_weight_right_3 or 0.0})

            # --- KB Squat ---
            KBSquatResult.objects.update_or_create(player=self, defaults={"result_left_1": self.kb_squat_weight_left_1 or 0.0, "result_right_1": self.kb_squat_weight_right_1 or 0.0, "result_left_2": self.kb_squat_weight_left_2 or 0.0, "result_right_2": self.kb_squat_weight_right_2 or 0.0, "result_left_3": self.kb_squat_weight_left_3 or 0.0, "result_right_3": self.kb_squat_weight_right_3 or 0.0})

            # --- One Kettlebell Press ---
            OneKettlebellPressResult.objects.update_or_create(player=self, defaults={"result_1": self.one_kb_press_weight_1 or 0.0, "result_2": self.one_kb_press_weight_2 or 0.0, "result_3": self.one_kb_press_weight_3 or 0.0})

            # --- Two Kettlebell Press ---
            TwoKettlebellPressResult.objects.update_or_create(player=self, defaults={"result_left_1": self.two_kb_press_weight_left_1 or 0.0, "result_right_1": self.two_kb_press_weight_right_1 or 0.0, "result_left_2": self.two_kb_press_weight_left_2 or 0.0, "result_right_2": self.two_kb_press_weight_right_2 or 0.0, "result_left_3": self.two_kb_press_weight_left_3 or 0.0, "result_right_3": self.two_kb_press_weight_right_3 or 0.0})

            # --- Aktualizacja wyników ogólnych ---
            # Upewnij się, że gracz ma przypisane kategorie, zanim wywołasz update
            if self.pk and self.categories.exists():
                 update_overall_results_for_player(self)
            # else:
            #      print(f"INFO: Player {self} nie ma kategorii, pomijam update_overall_results.")


        except Exception as e:
            print(f"!!!!!!!!!! BŁĄD Player {self.id} w update_related_results: {e} !!!!!!!!!!!")
            import traceback; traceback.print_exc()
        finally:
            self._updating_results = False

    def save(self, *args, **kwargs) -> None:
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if not getattr(self, "_updating_results", False):
            try: self.update_related_results()
            except Exception as e_update:
                print(f"!!!!!!!!! Player {self.id}: BŁĄD podczas update_related_results() z save(): {e_update} !!!!!!!!!")
                import traceback; traceback.print_exc()

    def calculate_snatch_score(self) -> float | None:
        weight = self.snatch_kettlebell_weight
        reps = self.snatch_repetitions
        if weight is not None and reps is not None and weight > 0 and reps > 0:
            return round(weight * reps, 1)
        return None
"""Model definition for OverallResult."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class OverallResult(models.Model):
    """
    Stores the calculated points per discipline, total points,
    and final position for a player across all disciplines in their categories.
    Points typically correspond to the player's position in that discipline (lower is better).
    """

    player = models.OneToOneField["Player"](
        "Player",
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="overallresult",
    )
    snatch_points = models.FloatField(_("Punkty Snatch"), null=True, blank=True)
    tgu_points = models.FloatField(_("Punkty TGU"), null=True, blank=True)
    see_saw_press_points = models.FloatField(_("Punkty See Saw Press"), null=True, blank=True)
    kb_squat_points = models.FloatField(_("Punkty Kettlebell Squat"), null=True, blank=True)
    pistol_squat_points = models.FloatField(_("Punkty Pistol Squat"), null=True, blank=True)
    one_kb_press_points = models.FloatField(_("Punkty One Kettlebell Press"), null=True, blank=True)
    two_kb_press_points = models.FloatField(_("Punkty Two Kettlebell Press"), null=True, blank=True)

    # Punkty karne za remis (np. -0.5) lub inne modyfikatory
    tiebreak_points = models.FloatField(_("Modyfikator/Dogrywka"), default=0.0)

    # Suma punktów (niżej = lepiej) - obliczana
    total_points = models.FloatField(_("Suma punktów"), null=True, blank=True, db_index=True)

    # Końcowa pozycja w kategorii (niżej = lepiej) - obliczana
    final_position = models.IntegerField(_("Pozycja Końcowa"), null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = _("Podsumowanie Wyników")
        verbose_name_plural = _("Podsumowania Wyników")
        ordering = ["final_position", "total_points", "player__surname"]  # Sortowanie

    def __str__(self) -> str:
        pos = f"Pos: {self.final_position}" if self.final_position is not None else "Pos: -"
        pts_val = getattr(self, "total_points", None)
        pts = f"Pts: {pts_val:.1f}" if pts_val is not None else "Pts: -"
        player_name = getattr(self.player, "full_name", "N/A")
        return f"{player_name} - Overall - {pos}, {pts}"

    def calculate_total_points(self) -> None:
        """
        Sums the points from all disciplines and the tiebreak points.
        Treats None as 0 for summation.
        Updates the instance's total_points attribute, does NOT save.
        """
        fields_to_sum = [
            self.snatch_points,
            self.tgu_points,
            self.see_saw_press_points,
            self.kb_squat_points,
            self.pistol_squat_points,
            self.one_kb_press_points,
            self.two_kb_press_points,
            self.tiebreak_points,
        ]
        # Sumuj punkty, traktując None jako 0.0
        total = sum(point or 0.0 for point in fields_to_sum)
        # Przypisz wynik lub None, jeśli wszystkie składniki były None (poza tiebreak)
        # (Chociaż suma 0.0 jest bardziej prawdopodobna i bezpieczniejsza)
        self.total_points = (
            round(total, 1) if total != 0.0 or self.tiebreak_points != 0.0 else 0.0
        )  # Można też dać None

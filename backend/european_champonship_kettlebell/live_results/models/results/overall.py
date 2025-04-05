from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import TYPE_CHECKING


class OverallResult(models.Model):
    """
    Stores the calculated points per discipline, total points,
    and final position for a player across all disciplines in their categories.
    """
    player = models.OneToOneField(
        "live_results.Player",
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="overallresult",
    )
    snatch_points = models.FloatField(_("Punkty Snatch"), null=True, blank=True)
    tgu_points = models.FloatField(_("Punkty TGU"), null=True, blank=True)
    see_saw_press_points = models.FloatField(_("Punkty See Saw Press"), null=True, blank=True)
    kb_squat_points = models.FloatField(_("Punkty Kettlebell Squat"), null=True, blank=True)
    pistol_squat_points = models.FloatField(_("Punkty Pistol Squat"), null=True, blank=True)
    one_kb_press_points = models.FloatField(_("Punkty One Kettlebell Press"), null=True, blank=True)
    two_kb_press_points = models.FloatField(_("Punkty Two Kettlebell Press"), null=True, blank=True)
    tiebreak_points = models.FloatField(_("Modyfikator/Dogrywka"), default=0.0)
    total_points = models.FloatField(_("Suma punktów"), null=True, blank=True, db_index=True)
    final_position = models.IntegerField(_("Pozycja Końcowa"), null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = _("Podsumowanie Wyników")
        verbose_name_plural = _("Podsumowania Wyników")
        ordering = ["final_position", "total_points", "player__surname"]

    def __str__(self) -> str:
        player_str = str(getattr(self, 'player', 'Brak gracza'))
        pos = f"Poz: {self.final_position}" if self.final_position is not None else "Poz: -"
        pts_val = getattr(self, "total_points", None)
        pts = f"Pkt: {pts_val:.1f}" if pts_val is not None else "Pkt: -"
        return f"{player_str} - Ogólnie - {pos}, {pts}"

    def calculate_total_points(self) -> None:
        """
        Sums the points from all disciplines and the tiebreak points.
        Treats None points as non-existent for sum. Saves the result to total_points.
        """
        fields_to_sum = [
            self.snatch_points, self.tgu_points, self.see_saw_press_points,
            self.kb_squat_points, self.pistol_squat_points, self.one_kb_press_points,
            self.two_kb_press_points
        ]
        # Sumuj tylko te punkty, które nie są None
        valid_points_sum = sum(point for point in fields_to_sum if point is not None)
        # Dodaj punkty tiebreak (które zawsze mają wartość, domyślnie 0.0)
        total = valid_points_sum + (self.tiebreak_points or 0.0)
        # Używamy round dla spójności, jeśli suma nie jest zerowa
        self.total_points = round(total, 1) if total != 0 or self.tiebreak_points != 0 else 0.0
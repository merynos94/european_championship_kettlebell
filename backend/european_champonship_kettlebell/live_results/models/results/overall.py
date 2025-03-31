# -*- coding: utf-8 -*-
"""Model definition for OverallResult."""
from typing import TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player # Dostosuj ścieżkę jeśli Player jest gdzie indziej

class OverallResult(models.Model):
    """
    Stores the calculated points per discipline, total points,
    and final position for a player across all disciplines in their categories.
    Points typically correspond to the player's position in that discipline (lower is better).
    """
    player = models.OneToOneField['Player'](
        'Player', # Użyj stringa
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="overallresult" # Django domyślnie użyje overallresult_set lub overallresult
    )
    # Punkty za pozycję w każdej dyscyplinie (niżej = lepiej)
    snatch_points = models.FloatField(_("Snatch Points (Position)"), null=True, blank=True, default=0.0)
    tgu_points = models.FloatField(_("TGU Points (Position)"), null=True, blank=True, default=0.0)
    see_saw_press_points = models.FloatField(_("See Saw Press Points (Position)"), null=True, blank=True, default=0.0)
    kb_squat_points = models.FloatField(_("KB Squat Points (Position)"), null=True, blank=True, default=0.0)
    pistol_squat_points = models.FloatField(_("Pistol Squat Points (Position)"), null=True, blank=True, default=0.0)

    # Punkty karne za remis (np. -0.5)
    tiebreak_points = models.FloatField(_("Tiebreak Points"), default=0.0)

    # Suma punktów (niżej = lepiej) - obliczana
    total_points = models.FloatField(_("Total Points"), null=True, blank=True, default=0.0, db_index=True) # Indeks dla szybszego sortowania

    # Końcowa pozycja w kategorii (niżej = lepiej) - obliczana
    final_position = models.IntegerField(_("Final Position"), null=True, blank=True, db_index=True) # Indeks dla szybszego sortowania

    class Meta:
        verbose_name = _("Overall Result")
        verbose_name_plural = _("Overall Results")
        # Domyślne sortowanie wg pozycji końcowej, potem wg sumy punktów
        ordering = ['final_position', 'total_points', 'player__surname']

    def __str__(self) -> str:
        pos = f"Pos: {self.final_position}" if self.final_position is not None else "Pos: N/A"
        pts = f"Pts: {self.total_points:.1f}" if self.total_points is not None else "Pts: N/A"
        return f"{self.player} - Overall - {pos}, {pts}"

    def calculate_total_points(self) -> None:
        """
        Sums the points from all disciplines and the tiebreak points.
        This method only updates the instance's total_points attribute, it does NOT save.
        Saving should be handled externally after calling this method.
        """
        # Użyj 0.0 jeśli punktacja dla dyscypliny to None
        total = (
            (self.snatch_points or 0.0) +
            (self.tgu_points or 0.0) +
            (self.see_saw_press_points or 0.0) +
            (self.kb_squat_points or 0.0) +
            (self.pistol_squat_points or 0.0) +
            (self.tiebreak_points or 0.0) # tiebreak_points domyślnie jest 0.0
        )
        self.total_points = round(total, 1) # Zaokrąglenie do 1 miejsca po przecinku

    # Celowo nie ma tu metody save(), aby uniknąć niekontrolowanych zapisów.
    # Logika przypisywania punktów i pozycji końcowej znajduje się w `services.py`.
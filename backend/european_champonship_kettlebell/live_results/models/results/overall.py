# live_results/models/results/overall.py (lub odpowiednia lokalizacja)

from django.db import models
from django.conf import settings # Lepszy sposób na odwołanie się do modelu Player
from django.utils.translation import gettext_lazy as _

class OverallResult(models.Model):
    """Stores the overall calculated results for a player."""

    player = models.OneToOneField(
        'live_results.Player', # Upewnij się, że ścieżka jest poprawna
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="overallresult" # Ważne dla logiki w services.py i admin.py
    )

    # --- Punkty za poszczególne dyscypliny (przechowują wartość 'position' z indywidualnych wyników) ---
    snatch_points = models.FloatField(_("Punkty Snatch"), null=True, blank=True)
    tgu_points = models.FloatField(_("Punkty TGU"), null=True, blank=True)
    see_saw_press_points = models.FloatField(_("Punkty SSP"), null=True, blank=True)
    kb_squat_points = models.FloatField(_("Punkty KB Squat"), null=True, blank=True)
    pistol_squat_points = models.FloatField(_("Punkty Pistol"), null=True, blank=True)
    one_kb_press_points = models.FloatField(_("Punkty OKBP"), null=True, blank=True)
    two_kb_press_points = models.FloatField(_("Punkty TKBP"), null=True, blank=True)

    # --- Punkty dodatkowe i wynik końcowy ---
    tiebreak_points = models.FloatField(_("Punkty Tiebreak"), default=0.0) # Obliczane w services.py
    total_points = models.FloatField(_("Suma Punktów"), null=True, blank=True, db_index=True) # Obliczane przez calculate_total_points
    final_position = models.PositiveIntegerField(_("Miejsce Końcowe"), null=True, blank=True, db_index=True) # Obliczane w services.py

    class Meta:
        verbose_name = _("Podsumowanie Wyników")
        verbose_name_plural = _("Podsumowania Wyników")
        ordering = ['final_position', 'total_points'] # Spójne z services.py

    def calculate_total_points(self):
        """
        Calculates the total points for the overall result.
        Sums the points (positions) from individual disciplines where points are not None.
        Adds tiebreak points. Lower total points mean better ranking.
        """
        points_to_sum = [
            self.snatch_points,
            self.tgu_points,
            self.see_saw_press_points,
            self.kb_squat_points,
            self.pistol_squat_points,
            self.one_kb_press_points,
            self.two_kb_press_points,
        ]

        # Filtrujemy wartości None (jeśli zawodnik nie ma pozycji w dyscyplinie)
        valid_points = [p for p in points_to_sum if p is not None]

        if not valid_points:
            # Brak jakichkolwiek punktów = brak wyniku ogólnego
            self.total_points = None
        else:
            # Sumujemy pozycje (jako punkty) i dodajemy punkty za tiebreak
            self.total_points = sum(valid_points) + (self.tiebreak_points or 0.0)

        # Ta metoda tylko oblicza wartość, zapis jest realizowany przez bulk_update w services.py

    def __str__(self):
        player_name = str(self.player) if hasattr(self, 'player') and self.player else "Brak Zawodnika"
        pos = self.final_position if self.final_position is not None else "N/A"
        pts = f"{self.total_points:.1f}" if self.total_points is not None else "N/A"
        return f"Wyniki: {player_name} - Miejsce: {pos}, Punkty: {pts}"
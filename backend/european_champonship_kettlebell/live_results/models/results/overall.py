from django.db import models
from django.utils.translation import gettext_lazy as _


class CategoryOverallResult(models.Model):
    """
    Przechowuje zagregowane wyniki i pozycję końcową zawodnika
    W KONKRETNEJ KATEGORII.
    """
    player = models.ForeignKey(
        "live_results.Player", # Dostosuj ścieżkę do modelu Player
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="category_results", # Możesz zmienić related_name jeśli chcesz
    )
    category = models.ForeignKey(
        "live_results.Category", # Dostosuj ścieżkę do modelu Category
        on_delete=models.CASCADE,
        verbose_name=_("Kategoria"),
        related_name="overall_results",
    )

    # Pola punktowe (miejsca z dyscyplin)
    snatch_points = models.FloatField(_("Punkty Snatch"), null=True, blank=True)
    tgu_points = models.FloatField(_("Punkty TGU"), null=True, blank=True)
    kb_squat_points = models.FloatField(_("Punkty KB Squat"), null=True, blank=True)
    one_kb_press_points = models.FloatField(_("Punkty OKBP"), null=True, blank=True)
    two_kb_press_points = models.FloatField(_("Punkty TKBP"), null=True, blank=True)
    # Dodaj/usuń pola zgodnie z aktywnymi dyscyplinami w Twoim systemie

    tiebreak_points = models.FloatField(_("Punkty Tiebreak"), default=0.0)
    total_points = models.FloatField(_("Suma Punktów"), null=True, blank=True, db_index=True)
    final_position = models.PositiveIntegerField(_("Miejsce Końcowe"), null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = _("Wynik Ogólny Kategorii")
        verbose_name_plural = _("Wyniki Ogólne Kategorii")
        # Unikalność dla pary zawodnik-kategoria
        unique_together = ('player', 'category')
        ordering = ["category", "final_position", "total_points"] # Domyślne sortowanie

    def calculate_total_points(self):
        """Oblicza sumę punktów (miejsc) dla tej kategorii."""
        points_to_sum = [
            self.snatch_points,
            self.tgu_points,
            self.kb_squat_points,
            self.one_kb_press_points,
            self.two_kb_press_points,
            # Dodaj/usuń pola punktowe
        ]
        # Sumujemy tylko te punkty, które nie są None
        valid_points = [p for p in points_to_sum if p is not None]
        # Sumujemy punkty (miejsca) i dodajemy tiebreak (-0.5 lub 0)
        # Niższa suma jest lepsza
        self.total_points = sum(valid_points) + (self.tiebreak_points or 0.0) if valid_points else None

    def __str__(self):
        player_name = str(self.player) if hasattr(self, "player") and self.player else "Brak Zawodnika"
        cat_name = str(self.category) if hasattr(self, "category") and self.category else "Brak Kategorii"
        pos = self.final_position if self.final_position is not None else "N/A"
        pts = f"{self.total_points:.1f}" if self.total_points is not None else "N/A"
        return f"Wyniki ({cat_name}): {player_name} - Miejsce: {pos}, Punkty: {pts}"
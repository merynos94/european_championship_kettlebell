from django.db import models
from django.utils.translation import gettext_lazy as _


class CategoryOverallResult(models.Model):
    player = models.ForeignKey("live_results.Player", on_delete=models.CASCADE, related_name="category_results", verbose_name=_("Zawodnik"))
    category = models.ForeignKey("live_results.Category", on_delete=models.CASCADE, related_name="overall_results", verbose_name=_("Kategoria"))
    snatch_points = models.FloatField(_("Punkty Snatch"), null=True, blank=True)
    tgu_points = models.FloatField(_("Punkty TGU"), null=True, blank=True)
    kb_squat_points = models.FloatField(_("Punkty KB Squat"), null=True, blank=True)
    one_kb_press_points = models.FloatField(_("Punkty OKBP"), null=True, blank=True)
    two_kb_press_points = models.FloatField(_("Punkty TKBP"), null=True, blank=True)
    tiebreak_points = models.FloatField(_("Punkty Tiebreak"), default=0.0)
    total_points = models.FloatField(_("Suma Punktów"), null=True, blank=True, db_index=True)
    final_position = models.PositiveIntegerField(_("Miejsce Końcowe"), null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = _("Wynik Ogólny Kategorii")
        verbose_name_plural = _("Wyniki Ogólne Kategorii")
        unique_together = ('player', 'category')
        ordering = ["category", "final_position", "total_points"]

    def calculate_total_points(self): # Bez zmian
        points_to_sum = [ self.snatch_points, self.tgu_points, self.kb_squat_points, self.one_kb_press_points, self.two_kb_press_points, ]
        valid_points = [p for p in points_to_sum if p is not None]
        self.total_points = sum(valid_points) + (self.tiebreak_points or 0.0) if valid_points else None

    def __str__(self): # Bez zmian
        player_name = str(self.player) if hasattr(self, "player") and self.player else "Brak Zawodnika"
        cat_name = str(self.category) if hasattr(self, "category") and self.category else "Brak Kategorii"
        pos = self.final_position if self.final_position is not None else "N/A"; pts = f"{self.total_points:.1f}" if self.total_points is not None else "N/A"
        return f"Wyniki ({cat_name}): {player_name} - Miejsce: {pos}, Punkty: {pts}"

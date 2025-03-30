from django.db import models


class AthleteCategory(models.Model):
    """
    Linking model connecting athletes with categories.
    Contains information about points, placements, and tiebreakers.
    """

    athlete = models.ForeignKey(
        "Athlete",
        on_delete=models.CASCADE,
        related_name="category_enrollments",  # This creates the reverse relation
        verbose_name="Zawodnik",
    )
    category = models.ForeignKey(
        "Category", on_delete=models.CASCADE, related_name="athlete_enrollments", verbose_name="Kategoria"
    )
    points = models.DecimalField(max_digits=5, decimal_places=1, default=0, verbose_name="Punkty")
    tiebreaker = models.BooleanField(default=False, verbose_name="Dogrywka (-0.5 pkt)")
    place = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Miejsce")

    def __str__(self):
        return f"{self.athlete} - {self.category}"

    class Meta:
        verbose_name = "Zawodnik w kategorii"
        verbose_name_plural = "Zawodnicy w kategoriach"
        unique_together = [["athlete", "category"]]

    def save(self, *args, **kwargs):
        """
        Override save method to automatically set points based on place.
        """
        if self.place is not None and self.place > 0:
            self.points = self.place
        super().save(*args, **kwargs)

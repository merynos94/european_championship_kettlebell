from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from .category import Category
from .club import Club


class AthleteManager(models.Manager):
    """
    Custom manager for the Athlete model providing additional query methods.
    """

    def get_ranking(self, category):
        """Return athletes ranked by points in a specific category."""
        return self.filter(category_enrollments__category=category).order_by("category_enrollments__points")

    def by_club(self, club):
        """Return all athletes from a specific club."""
        return self.filter(club=club)


class Athlete(models.Model):
    """
    Athlete model representing a competition participant.
    Contains personal data and references to categories through AthleteCategory.
    """

    first_name = models.CharField(max_length=100, verbose_name="Imię")
    last_name = models.CharField(max_length=100, verbose_name="Nazwisko")
    body_weight = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Waga ciała [kg]"
    )
    club = models.ForeignKey(
        Club, on_delete=models.SET_NULL, null=True, blank=True, related_name="athletes", verbose_name="Klub"
    )
    categories = models.ManyToManyField(
        Category,
        through="AthleteCategory",  # This specifies the through model
        related_name="athletes",
        verbose_name="Kategorie",
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Uwagi")

    # Use custom manager
    objects = AthleteManager()

    def __str__(self):
        club_name = self.club.name if self.club else "Brak klubu"
        return f"{self.first_name} {self.last_name} ({club_name})"

    class Meta:
        verbose_name = "Zawodnik"
        verbose_name_plural = "Zawodnicy"
        ordering = ["last_name", "first_name"]

    def get_total_points(self, category=None):
        """
        Calculate the total points for an athlete in a specific category.
        Lower points mean better result.
        """
        category_enrollments = self.filter(category=category) if category else self.category_enrollments.all()
        total = 0

        for enrollment in category_enrollments:
            # Sum points from each category
            total += enrollment.points

            # Apply tiebreaker if set
            if enrollment.tiebreaker:
                total -= 0.5

        return total

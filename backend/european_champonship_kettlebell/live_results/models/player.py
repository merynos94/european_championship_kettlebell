from django.db import models
from django.utils.translation import gettext_lazy as _


class Player(models.Model):
    """Represents a competitor."""

    name = models.CharField(_("Imię"), max_length=50)
    surname = models.CharField(_("Nazwisko"), max_length=50)
    weight = models.FloatField(_("Waga (kg)"), null=True, blank=True, default=0.0)
    club = models.ForeignKey(
        "live_results.SportClub",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Klub"),
        related_name="players",
    )
    categories = models.ManyToManyField(
        "live_results.Category", verbose_name=_("Kategorie"), related_name="players", blank=True
    )

    class Meta:
        verbose_name = _("Zawodnik")
        verbose_name_plural = _("Zawodnicy")
        ordering = ["surname", "name"]

    def __str__(self) -> str:
        return f"{self.name} {self.surname}"

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs) -> None:
        if self.weight is None:
            self.weight = 0.0
        super().save(*args, **kwargs)

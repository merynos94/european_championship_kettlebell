"""Model definition for SnatchResult."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class SnatchResult(models.Model):
    """Stores the result for the Snatch discipline."""

    player = models.OneToOneField["Player"](  # OneToOne jest bardziej odpowiednie jeśli jest tylko 1 wynik per gracz
        "Player",  # Użyj stringa dla uniknięcia importów
        on_delete=models.CASCADE,
        verbose_name=_("Zawodnik"),
        related_name="snatch_result",  # Zmieniono related_name
    )
    # Wynik jest teraz obliczany i zapisywany, nie potrzebujemy pól wejściowych tutaj
    result = models.FloatField(_("Wynik Snatch (Waga*Powt.)"), null=True, blank=True)
    position = models.IntegerField(_("Pozycja w konkurencji"), null=True, blank=True)  # Pozycja w ramach kategorii

    class Meta:
        verbose_name = _("Wynik Snatch")
        verbose_name_plural = _("Wyniki Snatch")
        # Sortowanie wg wyniku malejąco domyślnie?
        ordering = ["player__categories", "-result"]  # Przykład sortowania

    def __str__(self) -> str:
        score = f"{self.result:.1f}" if self.result is not None else _("N/A")
        return f"{self.player} - Snatch: {score}"

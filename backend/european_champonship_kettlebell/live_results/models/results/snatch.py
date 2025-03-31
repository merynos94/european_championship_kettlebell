# -*- coding: utf-8 -*-
"""Model definition for SnatchResult."""
from typing import Optional, TYPE_CHECKING
from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from ..player import Player # Zmien ścieżkę jeśli Player jest gdzie indziej

class SnatchResult(models.Model):
    """Stores the result for the Snatch discipline."""
    player = models.OneToOneField['Player']( # OneToOne jest bardziej odpowiednie jeśli jest tylko 1 wynik per gracz
        'Player', # Użyj stringa dla uniknięcia importów
        on_delete=models.CASCADE,
        verbose_name=_("Player"),
        related_name="snatch_result" # Zmieniono related_name
    )
    # Wynik jest teraz obliczany i zapisywany, nie potrzebujemy pól wejściowych tutaj
    result = models.FloatField(_("Snatch Score (Weight*Reps)"), null=True, blank=True)
    position = models.IntegerField(_("Position in Category"), null=True, blank=True) # Pozycja w ramach kategorii

    class Meta:
        verbose_name = _("Snatch Result")
        verbose_name_plural = _("Snatch Results")
        # Sortowanie wg wyniku malejąco domyślnie?
        ordering = ['player__categories', '-result'] # Przykład sortowania

    def __str__(self) -> str:
        score = f"{self.result:.1f}" if self.result is not None else _('N/A')
        return f"{self.player} - Snatch: {score}"
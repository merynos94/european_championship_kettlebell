# -*- coding: utf-8 -*-
"""Model definition for Category."""
from typing import List
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import AVAILABLE_DISCIPLINES, DISCIPLINE_NAMES

class Category(models.Model):
    """Represents a competition category with specific disciplines."""
    name = models.CharField(_("Category Name"), max_length=100, unique=True) # Dodano unique=True?
    disciplines = models.JSONField(_("Disciplines"), default=list)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def set_disciplines(self, disciplines: List[str]) -> None:
        """Sets the list of disciplines, ensuring they are valid."""
        valid_disciplines = [d[0] for d in AVAILABLE_DISCIPLINES]
        self.disciplines = sorted([d for d in disciplines if d in valid_disciplines]) # Sortowanie dla spójności
        # Usunięto self.save() - powinno być wywoływane z zewnątrz, np. w save() formularza/modelu

    def get_disciplines(self) -> List[str]:
        """Returns the list of disciplines for this category."""
        return self.disciplines

    def get_disciplines_display(self) -> str:
        """Returns a comma-separated string of human-readable discipline names."""
        return ", ".join(DISCIPLINE_NAMES.get(d, d) for d in self.disciplines)

    # Można rozważyć dodanie walidacji do clean() metody, jeśli używane w ModelForms
    # def clean(self):
    #     super().clean()
    #     valid_disciplines = [d[0] for d in AVAILABLE_DISCIPLINES]
    #     if not all(d in valid_disciplines for d in self.disciplines):
    #         raise ValidationError(_("Invalid discipline selected."))
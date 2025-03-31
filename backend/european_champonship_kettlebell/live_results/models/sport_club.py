# -*- coding: utf-8 -*-
"""Model definition for SportClub."""
from django.db import models
from django.utils.translation import gettext_lazy as _

class SportClub(models.Model):
    """Represents a sports club."""
    name = models.CharField(_("Club Name"), max_length=100, unique=True) # Dodano unique=True?

    class Meta:
        verbose_name = _("Sport Club")
        verbose_name_plural = _("Sport Clubs")
        ordering = ["name"] # Dobra praktyka - domyślne sortowanie

    def __str__(self) -> str:
        return self.name
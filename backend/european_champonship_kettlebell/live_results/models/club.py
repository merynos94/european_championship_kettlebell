from django.db import models


class Club(models.Model):
    """
    Club model representing the sports club of an athlete.
    Stores basic information about the club.
    """

    name = models.CharField(max_length=150, verbose_name="Nazwa klubu")
    address = models.TextField(blank=True, null=True, verbose_name="Adres")
    contact = models.CharField(max_length=200, blank=True, null=True, verbose_name="Kontakt")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Klub"
        verbose_name_plural = "Kluby"
        ordering = ["name"]

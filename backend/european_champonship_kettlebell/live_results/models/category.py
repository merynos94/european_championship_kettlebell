from django.db import models


class Category(models.Model):
    """
    Category model representing different competition categories.
    Examples include weight categories, age categories, etc.
    """

    name = models.CharField(max_length=100, verbose_name="Nazwa kategorii")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["name"]

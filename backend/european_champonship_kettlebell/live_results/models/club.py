from django.db import models


class Club(models.Model):
    """
    Club model representing the sports club of an athlete.
    Stores basic information about the club.
    """

    name = models.CharField(max_length=150, verbose_name="Nazwa klubu")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Klub"
        verbose_name_plural = "Kluby"
        ordering = ["name"]

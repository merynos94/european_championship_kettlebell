# live_results/resources.py

from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

# Importuj swoje modele
from .models import Category, Player, SportClub


class PlayerResource(resources.ModelResource):
    club = fields.Field(column_name="club", attribute="club", widget=ForeignKeyWidget(SportClub, "name"))
    categories = fields.Field(
        column_name="categories", attribute="categories", widget=ManyToManyWidget(Category, separator=",", field="name")
    )

    class Meta:
        model = Player
        # Wymień pola, które chcesz importować/eksportować
        fields = (
            "id",
            "name",
            "surname",
            "weight",
            "club",
            "categories",
            "tiebreak",
            # Dodaj pola wejściowe wyników, jeśli chcesz je importować/eksportować
            "snatch_kettlebell_weight",
            "snatch_repetitions",
            "tgu_weight_1",
            "tgu_weight_2",
            "tgu_weight_3",
            "see_saw_press_weight_left_1",
            "see_saw_press_weight_right_1",
            "see_saw_press_weight_left_2",
            "see_saw_press_weight_right_2",
            "see_saw_press_weight_left_3",
            "see_saw_press_weight_right_3",
            "kb_squat_weight_left_1",
            "kb_squat_weight_right_1",
            "kb_squat_weight_left_2",
            "kb_squat_weight_right_2",
            "kb_squat_weight_left_3",
            "kb_squat_weight_right_3",
            "pistol_squat_weight_1",
            "pistol_squat_weight_2",
            "pistol_squat_weight_3",
        )
        # Możesz też użyć exclude = (...)
        skip_unchanged = True  # Nie aktualizuj niezmienionych wierszy
        report_skipped = True  # Raportuj pominięte wiersze
        import_id_fields = ("id",)  # Użyj ID do identyfikacji istniejących graczy


# Możesz stworzyć osobne klasy dla importu i eksportu, jeśli potrzebujesz różnic
class PlayerImportResource(PlayerResource):
    pass


class PlayerExportResource(PlayerResource):
    pass

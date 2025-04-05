from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from .models import Category, Player, SportClub


class PlayerResource(resources.ModelResource):
    club = fields.Field(column_name="club", attribute="club", widget=ForeignKeyWidget(model=SportClub, field="name"))
    categories = fields.Field(
        column_name="categories",
        attribute="categories",
        widget=ManyToManyWidget(model=Category, separator=",", field="name"),
    )

    class Meta:
        model = Player
        fields = ("id", "name", "surname", "weight", "club", "categories")
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ("id",)


class PlayerImportResource(PlayerResource):
    def before_import_row(self, row, row_number=None, **kwargs):
        """
        Upewnia się, że klub i kategorie istnieją przed przetworzeniem wiersza.
        Jeśli nie istnieją, tworzy je.
        (Logika tworzenia klubu/kategorii pozostaje bez zmian)
        """
        club_name = row.get("club")
        if club_name:
            try:
                club, created = SportClub.objects.get_or_create(name=club_name.strip())
                if created:
                    print(f"Utworzono nowy klub: {club_name.strip()}")
            except Exception as e:
                print(f"Błąd przy tworzeniu/pobieraniu klubu '{club_name}' w wierszu {row_number}: {e}")

        categories_str = row.get("categories")
        if categories_str:
            category_names = [name.strip() for name in categories_str.split(",") if name.strip()]
            for cat_name in category_names:
                try:
                    category, created = Category.objects.get_or_create(name=cat_name)
                    if created:
                        print(f"Utworzono nową kategorię: {cat_name}")
                except Exception as e:
                    print(f"Błąd przy tworzeniu/pobieraniu kategorii '{cat_name}' w wierszu {row_number}: {e}")

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Pomija wiersz, jeśli gracz o tym samym imieniu i nazwisku już istnieje
        i ten wiersz *nie* jest aktualizacją istniejącego rekordu po ID.
        """
        is_new_instance = instance.pk is None

        if is_new_instance:
            name = row.get("name", "").strip()
            surname = row.get("surname", "").strip()

            if name and surname:
                exists = Player.objects.filter(name__iexact=name, surname__iexact=surname).exists()

                if exists:
                    print(f"POMIJANIE: Gracz '{name} {surname}' już istnieje. Wiersz: {row}")
                    return True

        return super().skip_row(instance, original, row, import_validation_errors)


class PlayerExportResource(PlayerResource):
    pass

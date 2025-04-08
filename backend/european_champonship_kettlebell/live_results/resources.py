from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget

from .models import Category, Player, SportClub


class PlayerResource(resources.ModelResource):
    """
    A resource class for handling the import and export of Player data.
    This class defines how Player data is mapped to and from external formats (e.g., CSV).
    """

    # Field for the player's club, using a ForeignKeyWidget to map the club name to the SportClub model.
    club = fields.Field(
        column_name="club",
        attribute="club",
        widget=ForeignKeyWidget(model=SportClub, field="name")
    )

    # Field for the player's categories, using a ManyToManyWidget to map category names to the Category model.
    categories = fields.Field(
        column_name="categories",
        attribute="categories",
        widget=ManyToManyWidget(model=Category, separator=",", field="name"),
    )

    class Meta:
        """
        Meta options for the PlayerResource class.
        - model: Specifies the Player model to use.
        - fields: Defines the fields to include in the import/export process.
        - skip_unchanged: Skips rows that have not changed during import.
        - report_skipped: Reports skipped rows during import.
        - import_id_fields: Specifies the fields used to identify records during import.
        """
        model = Player
        fields = ("id", "name", "surname", "weight", "club", "categories")
        skip_unchanged = True
        report_skipped = True
        import_id_fields = ("id",)


class PlayerImportResource(PlayerResource):
    """
    A specialized resource class for importing Player data.
    This class extends PlayerResource and adds custom logic for handling related objects
    (e.g., creating clubs and categories) and skipping duplicate rows.
    """

    def before_import_row(self, row, row_number=None, **kwargs):
        """
        Hook executed before importing each row.
        Ensures that related objects (clubs and categories) exist in the database.

        Args:
            row (dict): The data for the current row being imported.
            row_number (int, optional): The row number in the import file.
            **kwargs: Additional keyword arguments.
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
        Determines whether to skip a row during import.
        Skips rows if a player with the same name and surname already exists.

        Args:
            instance (Player): The Player instance being imported.
            original (Player): The original Player instance from the database.
            row (dict): The data for the current row being imported.
            import_validation_errors (list, optional): Validation errors for the row.

        Returns:
            bool: True if the row should be skipped, False otherwise.
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

    def after_save_instance(self, instance: Player, row, **kwargs):
        """
        Hook executed after saving each Player instance.
        Logs information about the saved instance and checks its categories.

        Args:
            instance (Player): The Player instance that was saved.
            row (dict): The data for the current row being imported.
            **kwargs: Additional keyword arguments.
        """
        dry_run = kwargs.get('dry_run', False)

        if not dry_run:
            print(f"[Import after_save] Zapisano instancję gracza ID: {instance.id} ({instance}).")
            print(f"[Import after_save DEBUG] Sprawdzanie kategorii dla Player ID: {instance.id} (w tym punkcie mogą jeszcze nie być zapisane M2M)")
            try:
                instance.refresh_from_db()
                db_cats = list(instance.categories.all())
                category_pks = set(c.pk for c in db_cats)
                print(f"[Import after_save DEBUG] Znalezione PK kategorii w after_save_instance: {category_pks}")
            except Exception as e_refresh:
                print(f"[Import after_save DEBUG] Błąd odświeżania instancji gracza {instance.id} w after_save: {e_refresh}")


class PlayerExportResource(PlayerResource):
    """
    A specialized resource class for exporting Player data.
    This class extends PlayerResource and does not add any additional functionality.
    """
    pass
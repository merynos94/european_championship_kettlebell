from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import F  # Import F for annotations
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

# === Import Models ===
# Importuj wszystko z modelu models
from .models import (
    # Constants
    AVAILABLE_DISCIPLINES,
    # Best Results
    BestKBSquatResult,
    BestOneKettlebellPressResult,  # Nowe
    BestPistolSquatResult,  # Nowe
    BestSeeSawPressResult,
    BestSnatchResult,  # Nowe
    BestTGUResult,  # Nowe
    BestTwoKettlebellPressResult,
    # Entities
    Category,
    # Raw Results
    KBSquatResult,
    OneKettlebellPressResult,
    # Overall
    OverallResult,
    PistolSquatResult,
    Player,
    SeeSawPressResult,
    SnatchResult,
    SportClub,
    TGUResult,
    TwoKettlebellPressResult,
)

# === Import Resources ===
# Dostosuj ścieżkę jeśli resources.py jest gdzie indziej
from .resources import PlayerExportResource, PlayerImportResource


# === Helper Functions ===
def player_link_display(obj, app_name="live_results"):  # Dodaj domyślną nazwę aplikacji
    """Generuje link HTML do strony zmiany gracza w adminie."""
    player = getattr(obj, "player", None)  # Bezpieczne pobranie gracza
    if player and player.pk:
        link = reverse(f"admin:{app_name}_player_change", args=[player.id])
        return format_html('<a href="{}">{}</a>', link, player)
    # Obsługa sytuacji, gdy obiekt nie ma gracza (np. testy, błędy danych)
    elif isinstance(obj, Player) and obj.pk:  # Jeśli obiektem jest sam Player
        link = reverse(f"admin:{app_name}_player_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', link, obj)
    return _("Brak gracza")


def get_player_categories_display(obj) -> str:
    """Zwraca string z kategoriami gracza powiązanego z obiektem."""
    player = getattr(obj, "player", None)
    if player and player.pk and hasattr(player, "categories"):
        return ", ".join([c.name for c in player.categories.all()])
    elif isinstance(obj, Player) and hasattr(obj, "categories"):  # Jeśli obiektem jest sam Player
        return ", ".join([c.name for c in obj.categories.all()])
    return "---"


# === Forms ===
class CategoryAdminForm(forms.ModelForm):
    disciplines = forms.MultipleChoiceField(
        choices=AVAILABLE_DISCIPLINES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Dyscypliny"),
        help_text=_("Wybierz dyscypliny dla tej kategorii."),
    )

    class Meta:
        model = Category
        fields = ["name", "disciplines"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["disciplines"].initial = self.instance.get_disciplines()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.set_disciplines(self.cleaned_data["disciplines"])
        if commit:
            instance.save()
        return instance


# === Model Admins ===


# --- Player Admin ---
@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    resource_classes = [PlayerImportResource]
    export_resource_classes = [PlayerExportResource]

    list_display = (
        "full_name",
        "weight",
        "club",
        "get_categories_for_player",  # Używa helpera dla spójności
        # Zmienione na 'best' results
        "get_best_snatch_display",
        "get_best_tgu_display",
        "get_best_ssp_display",
        "get_best_kbs_display",
        "get_best_pistol_squat_display",
        "get_best_one_kb_press_display",
        "get_best_two_kb_press_display",
        "tiebreak",
    )
    list_filter = ("club", "categories", "tiebreak", ("weight", admin.EmptyFieldListFilter))
    search_fields = ("name", "surname", "club__name", "categories__name")

    # Pola wejściowe pozostają bez zmian
    fieldsets = (
        (_("Dane Podstawowe"), {"fields": ("name", "surname", "weight", "club", "categories", "tiebreak")}),
        (_("Snatch"), {"fields": ("snatch_kettlebell_weight", "snatch_repetitions")}),
        (_("TGU"), {"fields": ("tgu_weight_1", "tgu_weight_2", "tgu_weight_3")}),
        (
            _("One Kettlebell Press"),
            {"fields": ("one_kb_press_weight_1", "one_kb_press_weight_2", "one_kb_press_weight_3")},
        ),
        (
            _("Two Kettlebell Press"),
            {
                "fields": (
                    ("two_kb_press_weight_left_1", "two_kb_press_weight_right_1"),
                    ("two_kb_press_weight_left_2", "two_kb_press_weight_right_2"),
                    ("two_kb_press_weight_left_3", "two_kb_press_weight_right_3"),
                )
            },
        ),
        (
            _("See Saw Press"),
            {
                "fields": (
                    ("see_saw_press_weight_left_1", "see_saw_press_weight_right_1"),
                    ("see_saw_press_weight_left_2", "see_saw_press_weight_right_2"),
                    ("see_saw_press_weight_left_3", "see_saw_press_weight_right_3"),
                )
            },
        ),
        (
            _("KB Squat"),
            {
                "fields": (
                    ("kb_squat_weight_left_1", "kb_squat_weight_right_1"),
                    ("kb_squat_weight_left_2", "kb_squat_weight_right_2"),
                    ("kb_squat_weight_left_3", "kb_squat_weight_right_3"),
                )
            },
        ),
        (
            _("Pistol Squat"),
            {
                "fields": (
                    "pistol_squat_weight_1",
                    "pistol_squat_weight_2",
                    "pistol_squat_weight_3",
                )
            },
        ),
        # Sekcja Read-Only zaktualizowana
        (
            _("Najlepsze Wyniki Obliczone (Tylko do odczytu)"),
            {
                "classes": ("collapse",),
                "fields": (
                    "get_best_snatch_display",
                    "get_best_tgu_display",
                    "get_best_ssp_display",
                    "get_best_kbs_display",
                    "get_best_pistol_squat_display",
                    "get_best_one_kb_press_display",
                    "get_best_two_kb_press_display",
                    "get_overall_score_display",  # Wynik ogólny
                ),
            },
        ),
    )

    # Zaktualizowane pola tylko do odczytu
    readonly_fields = (
        "get_best_snatch_display",
        "get_best_tgu_display",
        "get_best_ssp_display",
        "get_best_kbs_display",
        "get_best_pistol_squat_display",
        "get_best_one_kb_press_display",
        "get_best_two_kb_press_display",
        "get_overall_score_display",
    )

    # --- Metody Display dla PlayerAdmin ---
    @admin.display(description=_("Kategorie"))
    def get_categories_for_player(self, obj: Player) -> str:
        # Używa helpera zdefiniowanego wyżej
        return get_player_categories_display(obj)

    @admin.display(description=_("Najlepszy Snatch"))
    def get_best_snatch_display(self, obj: Player) -> str:
        try:
            res = obj.best_snatch_result  # Użyj related_name z BestSnatchResult
            score = res.best_result
            return f"{score:.1f}" if score is not None else "---"
        except BestSnatchResult.DoesNotExist:
            return "---"
        except AttributeError:  # Na wypadek gdyby obiekt nie był Player
            return "---"

    @admin.display(description=_("Najlepszy TGU"))
    def get_best_tgu_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z BestTGUResult
            return f"{obj.best_tgu_result.best_result:.1f}"
        except BestTGUResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy SSP (%)"))
    def get_best_ssp_display(self, obj: Player) -> str:
        try:
            # Updated to use best_result instead of best_left/best_right
            res = obj.best_see_saw_press_result
            return f"{res.best_result:.1f}%" if res.best_result is not None else "---"
        except BestSeeSawPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy KB Squat (Suma)"))
    def get_best_kbs_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z BestKBSquatResult
            return f"{obj.best_kb_squat_result.best_result:.1f}"
        except BestKBSquatResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy Pistol Squat"))
    def get_best_pistol_squat_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z BestPistolSquatResult
            return f"{obj.best_pistol_squat_result.best_result:.1f}"
        except BestPistolSquatResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy One KB Press"))
    def get_best_one_kb_press_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z BestOneKettlebellPressResult
            return f"{obj.best_one_kettlebell_press_result.best_result:.1f}"
        except BestOneKettlebellPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy Two KB Press (Suma)"))
    def get_best_two_kb_press_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z BestTwoKettlebellPressResult
            return f"{obj.best_two_kettlebell_press_result.best_result:.1f}"
        except BestTwoKettlebellPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Wynik Ogólny"))
    def get_overall_score_display(self, obj: Player) -> str:
        try:
            # Użyj related_name z OverallResult (domyślnie 'overallresult')
            return f"{obj.overallresult.total_points:.1f}"
        except OverallResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    # Metody import/export bez zmian
    def get_import_resource_classes(self, request):
        return [PlayerImportResource]

    def get_export_resource_classes(self, request):
        return [PlayerExportResource]

    # W pliku admin.py
    # Wewnątrz klasy PlayerAdmin(ImportExportModelAdmin):

    def save_model(self, request, obj, form, change):
        """Nadpisana metoda zapisu modelu w adminie dla debugowania."""
        print(f"==== PlayerAdmin: WYWOŁANO save_model dla gracza {obj} ====")  # <-- DODAJ TEN PRINT
        try:
            # Wywołaj domyślne zachowanie (które powinno wywołać obj.save())
            super().save_model(request, obj, form, change)
            print(f"==== PlayerAdmin: super().save_model() ZAKOŃCZONE dla gracza {obj} ====")  # <-- DODAJ TEN PRINT
        except Exception as e:
            print(f"!!!!!!!!! PlayerAdmin: BŁĄD w super().save_model(): {e} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            raise  # Rzuć błąd dalej, aby admin go obsłużył


# --- SportClub Admin ---
@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ("name", "player_count_display")  # Użycie nowej nazwy metody
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Użyj Count z odpowiednim related_name (domyślnie 'player_set')
        qs = qs.annotate(player_count_annotation=models.Count("players"))
        return qs

    @admin.display(description=_("Liczba Zawodników"), ordering="player_count_annotation")
    def player_count_display(self, obj: SportClub) -> int:  # Nowa nazwa metody
        # Odczytuje adnotację
        return getattr(obj, "player_count_annotation", 0)  # Bezpieczny odczyt


# --- Category Admin ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "get_disciplines_list_display")
    search_fields = ("name",)

    @admin.display(description=_("Dyscypliny"))
    def get_disciplines_list_display(self, obj: Category) -> str:
        # Użyj metody z modelu Category
        return obj.get_disciplines_display()


# --- Base Admin for Raw Results (with attempts) ---
class BaseResultAttemptAdmin(admin.ModelAdmin):
    """Klasa bazowa dla adminów wyników z podejściami (TGU, Pistol, OnePress)."""

    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = (
        "player_link",
        "position",
        "get_max_result_display",
        "get_bw_percentage_display",
        "get_player_categories",
    )
    list_select_related = ("player", "player__club")  # Optymalizacja

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj):
        return player_link_display(obj)

    @admin.display(description=_("Max Wynik"), ordering="max_result_value")  # Changed ordering field
    def get_max_result_display(self, obj) -> str:
        # Use the property from model, which already exists
        try:
            return f"{obj.max_result:.1f}"
        except AttributeError:
            return "N/A"  # In case property doesn't exist

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str | None:
        # Używamy property z modelu
        try:
            bw = obj.bw_percentage
            return f"{bw:.2f}%" if bw is not None else "---"
        except AttributeError:
            return "N/A"

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str:
        return get_player_categories_display(obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Don't use an annotation named 'max_result' as it conflicts with the property
        # Rename it to 'max_result_value' or something similar
        qs = qs.annotate(max_result_value=Greatest(F("result_1"), F("result_2"), F("result_3")))
        return qs


# --- Base Admin for Raw Results (L/R attempts) ---
class BaseResultLRAttemptAdmin(admin.ModelAdmin):
    """Klasa bazowa dla adminów wyników z podejściami L/R (SSP, KBSquat, TwoPress)."""

    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = (
        "player_link",
        "position",
        "get_max_score_display",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_bw_percentage_display",
        "get_player_categories",  # Dodano BW% i kategorie
    )
    list_select_related = ("player", "player__club")

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj):
        return player_link_display(obj)

    @admin.display(description=_("Próba 1 (L/R)"))
    def get_attempt_1_display(self, obj) -> str:
        # Zakładamy, że pola nazywają się result_left_1, result_right_1
        l = getattr(obj, "result_left_1", 0.0)
        r = getattr(obj, "result_right_1", 0.0)
        return f"{l:.1f} / {r:.1f}"

    @admin.display(description=_("Próba 2 (L/R)"))
    def get_attempt_2_display(self, obj) -> str:
        l = getattr(obj, "result_left_2", 0.0)
        r = getattr(obj, "result_right_2", 0.0)
        return f"{l:.1f} / {r:.1f}"

    @admin.display(description=_("Próba 3 (L/R)"))
    def get_attempt_3_display(self, obj) -> str:
        l = getattr(obj, "result_left_3", 0.0)
        r = getattr(obj, "result_right_3", 0.0)
        return f"{l:.1f} / {r:.1f}"

    @admin.display(description=_("Max Wynik (Suma)"), ordering="max_score")  # Zakłada adnotację max_score
    def get_max_score_display(self, obj) -> str:
        # Używamy property 'max_score' z modelu
        try:
            return f"{obj.max_score:.1f}"
        except AttributeError:
            # Awaryjne obliczenie, jeśli property nie istnieje lub queryset nie ma adnotacji
            score1 = obj.get_attempt_score(1) if hasattr(obj, "get_attempt_score") else 0
            score2 = obj.get_attempt_score(2) if hasattr(obj, "get_attempt_score") else 0
            score3 = obj.get_attempt_score(3) if hasattr(obj, "get_attempt_score") else 0
            return f"{max(score1, score2, score3):.1f}"

    @admin.display(description=_("% Masy Ciała"))  # Dodano BW%
    def get_bw_percentage_display(self, obj) -> str | None:
        # Używamy property z modelu, jeśli istnieje
        try:
            bw = obj.bw_percentage
            return f"{bw:.2f}%" if bw is not None else "---"
        except AttributeError:
            # Można dodać logikę obliczania BW% dla wyników L+R, jeśli potrzebne
            return "N/A"

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str:
        return get_player_categories_display(obj)


@admin.register(SnatchResult)
class SnatchResultAdmin(admin.ModelAdmin):  # Snatch jest prostszy
    list_display = ("player_link", "result", "position", "get_player_categories")
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("player_link", "position", "get_player_categories")  # result jest edytowalny?
    list_select_related = ("player", "player__club")

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: SnatchResult):
        return player_link_display(obj)

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: SnatchResult) -> str:
        return get_player_categories_display(obj)


@admin.register(TGUResult)
class TGUResultAdmin(BaseResultAttemptAdmin):
    list_display = (
        "player_link",
        "result_1",
        "result_2",
        "result_3",
        "get_max_result_display",
        "get_bw_percentage_display",
        "position",
        "get_player_categories",
    )


@admin.register(OneKettlebellPressResult)
class OneKettlebellPressResultAdmin(BaseResultAttemptAdmin):
    list_display = (
        "player_link",
        "result_1",
        "result_2",
        "result_3",
        "get_max_result_display",
        "get_bw_percentage_display",
        "position",
        "get_player_categories",
    )


@admin.register(PistolSquatResult)
class PistolSquatResultAdmin(BaseResultAttemptAdmin):
    list_display = (
        "player_link",
        "result_1",
        "result_2",
        "result_3",
        "get_max_result_display",
        "get_bw_percentage_display",
        "position",
        "get_player_categories",
    )


@admin.register(SeeSawPressResult)
class SeeSawPressResultAdmin(BaseResultLRAttemptAdmin):
    list_display = (
        "player_link",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_max_score_display",  # BW% jest w readonly_fields
        "position",
        "get_player_categories",
    )


@admin.register(KBSquatResult)
class KBSquatResultAdmin(BaseResultLRAttemptAdmin):
    list_display = (
        "player_link",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_max_score_display",  # BW% jest w readonly_fields
        "position",
        "get_player_categories",
    )


@admin.register(TwoKettlebellPressResult)
class TwoKettlebellPressResultAdmin(BaseResultLRAttemptAdmin):
    list_display = (
        "player_link",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_max_score_display",
        "get_bw_percentage_display",  # BW% jest istotne tutaj
        "position",
        "get_player_categories",
    )


# --- Overall Result Admin ---
@admin.register(OverallResult)
class OverallResultAdmin(admin.ModelAdmin):
    list_display = (
        "player_link",
        "get_player_categories",
        "snatch_points",
        "tgu_points",
        "see_saw_press_points",
        "kb_squat_points",
        "pistol_squat_points",
        "one_kb_press_points",
        "two_kb_press_points",
        "tiebreak_points",
        "total_points",
        "final_position",
    )
    ordering = ("final_position", "-total_points")  # Sortowanie wg pozycji, potem punktów

    readonly_fields = (  # Wszystkie pola są obliczane
        "player_link",
        "get_player_categories",
        "snatch_points",
        "tgu_points",
        "see_saw_press_points",
        "kb_squat_points",
        "pistol_squat_points",
        "one_kb_press_points",
        "two_kb_press_points",
        "tiebreak_points",
        "total_points",
        "final_position",
    )
    list_select_related = ("player", "player__club")  # Pobierz player i club przez JOIN
    list_prefetch_related = ("player__categories",)  # Pobierz kategorie w osobnym zapytaniu

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: OverallResult):
        return player_link_display(obj)

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: OverallResult) -> str:
        return get_player_categories_display(obj)

    # Wyniki ogólne też są tylko do odczytu
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

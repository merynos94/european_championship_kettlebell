from django import forms
from django.contrib import admin
from django.db import models
from django.db.models.functions import Greatest
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

# Importuj wszystko z nowego pakietu models
from .models import (
    AVAILABLE_DISCIPLINES,
    BestKBSquatResult,
    BestSeeSawPressResult,
    Category,
    KBSquatResult,
    OverallResult,
    PistolSquatResult,
    Player,
    SeeSawPressResult,
    SnatchResult,
    SportClub,
    TGUResult,
    # Nie importuj DISCIPLINE_NAMES jeśli nie jest tu używane
)

# Importuj zasoby import/export (zakładam, że plik resources.py istnieje)
# Dostosuj ścieżkę jeśli resources.py jest gdzie indziej
from .resources import PlayerExportResource, PlayerImportResource


# --- Formularz dla Category Admin ---
class CategoryAdminForm(forms.ModelForm):
    # Używamy stałej zaimportowanej z models
    disciplines = forms.MultipleChoiceField(
        choices=AVAILABLE_DISCIPLINES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Disciplines"),
        help_text=_("Select disciplines for this category."),
    )

    class Meta:
        model = Category
        fields = ["name", "disciplines"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicjalizacja pola disciplines z modelu
        if self.instance and self.instance.pk:
            self.fields["disciplines"].initial = self.instance.get_disciplines()

    def save(self, commit=True):
        # Zapisz najpierw instancję, aby mieć PK
        instance = super().save(commit=False)
        # Użyj metody set_disciplines z modelu (która już nie zapisuje)
        instance.set_disciplines(self.cleaned_data["disciplines"])
        if commit:
            instance.save()
            # self.save_m2m() # Nie jest potrzebne dla JSONField
        return instance


# --- Admin dla Player ---
@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    # Zasoby import/export
    resource_classes = [PlayerImportResource]  # Użyj resource_classes od Django 4.x
    export_resource_classes = [PlayerExportResource]  # Nowsza składnia

    list_display = (
        "full_name",  # Użyj property full_name
        "weight",
        "club",
        "get_categories_display",  # Zmieniona nazwa dla jasności
        "get_snatch_score_display",  # Pobierz wynik ze SnatchResult
        "get_tgu_max_display",  # Pobierz max z TGUResult
        "get_best_ssp_display",  # Pobierz best z BestSeeSawPressResult
        "get_best_kbs_display",  # Pobierz best z BestKBSquatResult
        "get_max_pistol_display",  # Pobierz max z PistolSquatResult
        "tiebreak",
    )
    list_filter = ("club", "categories", "tiebreak")
    search_fields = ("name", "surname", "club__name", "categories__name")
    # Dodaj filtrowanie wg wagi
    list_filter = ("club", "categories", "tiebreak", ("weight", admin.EmptyFieldListFilter))

    # Fieldsets odnoszą się do pól *wejściowych* na modelu Player.
    # To jest OK, dopóki te pola istnieją na Player.
    fieldsets = (
        (_("Basic Info"), {"fields": ("name", "surname", "weight", "club", "categories", "tiebreak")}),
        (_("Snatch Input"), {"fields": ("snatch_kettlebell_weight", "snatch_repetitions")}),
        (_("TGU Input"), {"fields": ("tgu_weight_1", "tgu_weight_2", "tgu_weight_3")}),
        (
            _("See Saw Press Input"),
            {
                "fields": (
                    ("see_saw_press_weight_left_1", "see_saw_press_weight_right_1"),
                    ("see_saw_press_weight_left_2", "see_saw_press_weight_right_2"),
                    ("see_saw_press_weight_left_3", "see_saw_press_weight_right_3"),
                )
            },
        ),
        (
            _("KB Squat Input"),
            {
                "fields": (
                    ("kb_squat_weight_left_1", "kb_squat_weight_right_1"),
                    ("kb_squat_weight_left_2", "kb_squat_weight_right_2"),
                    ("kb_squat_weight_left_3", "kb_squat_weight_right_3"),
                )
            },
        ),
        (
            _("Pistol Squat Input"),
            {
                "fields": (
                    "pistol_squat_weight_1",
                    "pistol_squat_weight_2",
                    "pistol_squat_weight_3",
                )
            },
        ),
        # Można dodać sekcję z wynikami tylko do odczytu
        (
            _("Calculated Results (Read-Only)"),
            {
                "classes": ("collapse",),  # Zwinięta domyślnie
                "fields": (
                    "get_snatch_score_display",
                    "get_tgu_max_display",
                    "get_best_ssp_display",
                    "get_best_kbs_display",
                    "get_max_pistol_display",
                    "get_overall_score_display",
                ),
            },
        ),
    )

    # Pola tylko do odczytu dla wyliczonych wyników w sekcji 'Calculated Results'
    readonly_fields = (
        "get_snatch_score_display",
        "get_tgu_max_display",
        "get_best_ssp_display",
        "get_best_kbs_display",
        "get_max_pistol_display",
        "get_overall_score_display",
    )

    # Metody do wyświetlania danych z powiązanych modeli
    @admin.display(description=_("Categories"))
    def get_categories_display(self, obj: Player) -> str:
        return ", ".join([cat.name for cat in obj.categories.all()])

    @admin.display(description=_("Snatch Score"))
    def get_snatch_score_display(self, obj: Player) -> str | None:
        try:
            score = obj.snatch_result.result
            return f"{score:.1f}" if score is not None else "---"
        except SnatchResult.DoesNotExist:
            return "---"

    @admin.display(description=_("TGU Max"))
    def get_tgu_max_display(self, obj: Player) -> str:
        try:
            return f"{obj.tgu_result.max_result:.1f}"
        except TGUResult.DoesNotExist:
            return "---"

    @admin.display(description=_("Best SSP (L/R)"))
    def get_best_ssp_display(self, obj: Player) -> str:
        try:
            res = obj.best_see_saw_press_result
            return f"{res.best_left:.1f} / {res.best_right:.1f}"
        except BestSeeSawPressResult.DoesNotExist:
            return "---"

    @admin.display(description=_("Best KBS"))
    def get_best_kbs_display(self, obj: Player) -> str:
        try:
            return f"{obj.best_kb_squat_result.best_result:.1f}"
        except BestKBSquatResult.DoesNotExist:
            return "---"

    @admin.display(description=_("Pistol Max"))
    def get_max_pistol_display(self, obj: Player) -> str:
        try:
            # Pistol nie ma modelu Best*, więc bierzemy max z PistolSquatResult
            return f"{obj.pistol_squat_result.max_result:.1f}"
        except PistolSquatResult.DoesNotExist:
            return "---"
        # Lub jeśli pola są nadal na Player:
        # return f"{obj.get_max_pistol_squat_weight():.1f}"

    @admin.display(description=_("Overall Score"))
    def get_overall_score_display(self, obj: Player) -> str:
        try:
            # Zakładając, że OverallResult ma pole total_points
            return f"{obj.overallresult.total_points:.1f}"
        except OverallResult.DoesNotExist:
            return "---"

    # Usunięto save_model - logika przeniesiona do Player.save() -> update_related_results()

    # Metody import/export bez zmian
    def get_import_resource_classes(self):
        return [PlayerImportResource]

    def get_export_resource_classes(self):
        return [PlayerExportResource]


# --- Admin dla SportClub ---
@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ("name", "player_count")
    search_fields = ("name",)

    @admin.display(description=_("Number of Players"))
    def player_count(self, obj: SportClub) -> int:
        # Można zoptymalizować przez annotację w get_queryset
        return obj.players.count()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(player_count_annotation=models.Count("players"))
        return qs

    @admin.display(description=_("Number of Players"), ordering="player_count_annotation")
    def player_count(self, obj: SportClub) -> int:
        return obj.player_count_annotation


# --- Admin dla Category ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm  # Użyj zmodyfikowanego formularza
    list_display = ("name", "get_disciplines_list_display")  # Użyj metody z modelu
    search_fields = ("name",)

    @admin.display(description=_("Disciplines"))
    def get_disciplines_list_display(self, obj: Category) -> str:
        # Użyj metody z modelu Category
        return obj.get_disciplines_display()


# --- Admin dla Wyników (Odkomentowane i Ulepszone) ---


@admin.register(SnatchResult)
class SnatchResultAdmin(admin.ModelAdmin):
    list_display = ("player_link", "result", "position", "get_player_categories")
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname")
    readonly_fields = ("player_link", "position")  # Pozycja jest obliczana
    list_select_related = ("player",)  # Optymalizacja zapytania

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: SnatchResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])  # Zmień 'twoja_aplikacja'
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: SnatchResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])


@admin.register(TGUResult)
class TGUResultAdmin(admin.ModelAdmin):
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
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname")
    readonly_fields = ("player_link", "position", "get_max_result_display", "get_bw_percentage_display")
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: TGUResult):
        # Jak wyżej...
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Max Result"), ordering="max_result")  # Zakładamy adnotację max_result w queryset
    def get_max_result_display(self, obj: TGUResult) -> str:
        return f"{obj.max_result:.1f}"  # Użyj property z modelu

    @admin.display(description=_("%BW"))
    def get_bw_percentage_display(self, obj: TGUResult) -> str | None:
        bw = obj.bw_percentage  # Użyj property z modelu
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: TGUResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    def get_queryset(self, request):
        # Adnotacja dla sortowania wg max_result
        qs = super().get_queryset(request)
        qs = qs.annotate(max_result=Greatest("result_1", "result_2", "result_3"))
        return qs


@admin.register(PistolSquatResult)
class PistolSquatResultAdmin(admin.ModelAdmin):
    # Podobnie jak TGUResultAdmin...
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
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname")
    readonly_fields = ("player_link", "position", "get_max_result_display", "get_bw_percentage_display")
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: PistolSquatResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Max Result"), ordering="max_result")
    def get_max_result_display(self, obj: PistolSquatResult) -> str:
        return f"{obj.max_result:.1f}"

    @admin.display(description=_("%BW"))
    def get_bw_percentage_display(self, obj: PistolSquatResult) -> str | None:
        bw = obj.bw_percentage
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: PistolSquatResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(max_result=Greatest("result_1", "result_2", "result_3"))
        return qs


@admin.register(SeeSawPressResult)
class SeeSawPressResultAdmin(admin.ModelAdmin):
    list_display = (
        "player_link",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_max_score_display",
        "position",
        "get_player_categories",
    )
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname")
    readonly_fields = (
        "player_link",
        "position",
        "get_max_score_display",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
    )
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: SeeSawPressResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Attempt 1 (L/R)"))
    def get_attempt_1_display(self, obj: SeeSawPressResult) -> str:
        return f"{obj.result_left_1:.1f} / {obj.result_right_1:.1f}"

    @admin.display(description=_("Attempt 2 (L/R)"))
    def get_attempt_2_display(self, obj: SeeSawPressResult) -> str:
        return f"{obj.result_left_2:.1f} / {obj.result_right_2:.1f}"

    @admin.display(description=_("Attempt 3 (L/R)"))
    def get_attempt_3_display(self, obj: SeeSawPressResult) -> str:
        return f"{obj.result_left_3:.1f} / {obj.result_right_3:.1f}"

    @admin.display(description=_("Max Score"), ordering="max_score")  # Zakłada adnotację
    def get_max_score_display(self, obj: SeeSawPressResult) -> str:
        return f"{obj.max_score:.1f}"  # Użyj property z modelu

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: SeeSawPressResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    # Potrzebna adnotacja dla sortowania wg max_score
    # def get_queryset(self, request):
    #      qs = super().get_queryset(request)
    #      # Dodaj adnotację max_score obliczoną podobnie jak w services.py
    #      # ...
    #      return qs


@admin.register(KBSquatResult)
class KBSquatResultAdmin(admin.ModelAdmin):
    # Podobnie do SeeSawPressResultAdmin...
    list_display = (
        "player_link",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
        "get_max_score_display",
        "position",
        "get_player_categories",
    )
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname")
    readonly_fields = (
        "player_link",
        "position",
        "get_max_score_display",
        "get_attempt_1_display",
        "get_attempt_2_display",
        "get_attempt_3_display",
    )
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: KBSquatResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Attempt 1 (L/R)"))
    def get_attempt_1_display(self, obj: KBSquatResult) -> str:
        return f"{obj.result_left_1:.1f} / {obj.result_right_1:.1f}"

    @admin.display(description=_("Attempt 2 (L/R)"))
    def get_attempt_2_display(self, obj: KBSquatResult) -> str:
        return f"{obj.result_left_2:.1f} / {obj.result_right_2:.1f}"

    @admin.display(description=_("Attempt 3 (L/R)"))
    def get_attempt_3_display(self, obj: KBSquatResult) -> str:
        return f"{obj.result_left_3:.1f} / {obj.result_right_3:.1f}"

    @admin.display(description=_("Max Score"), ordering="max_score")  # Zakłada adnotację
    def get_max_score_display(self, obj: KBSquatResult) -> str:
        return f"{obj.max_score:.1f}"

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: KBSquatResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    # def get_queryset(self, request):
    #      qs = super().get_queryset(request)
    #      # Dodaj adnotację max_score
    #      # ...
    #      return qs


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
        "tiebreak_points",
        "total_points",
        "final_position",
    )
    # Sortowanie domyślne wg pozycji końcowej
    ordering = ("final_position", "total_points")
    list_filter = ("player__categories", "final_position")
    search_fields = ("player__name", "player__surname", "player__categories__name")
    readonly_fields = (  # Wszystkie pola są obliczane
        "player_link",
        "snatch_points",
        "tgu_points",
        "see_saw_press_points",
        "kb_squat_points",
        "pistol_squat_points",
        "tiebreak_points",
        "total_points",
        "final_position",
        "get_player_categories",
    )
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: OverallResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: OverallResult) -> str:
        # Można by dodać filtrowanie OverallResult tylko do jednej kategorii
        # na widoku listy, jeśli to potrzebne.
        return ", ".join([c.name for c in obj.player.categories.all()])

    # Ta klasa admin nie powinna pozwalać na edycję, bo wyniki są kalkulowane.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Można zezwolić na widok, ale nie na zmianę
        return False  # lub return request.method == 'GET' dla Django < 5.0 (?)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BestSeeSawPressResult)
class BestSeeSawPressResultAdmin(admin.ModelAdmin):
    list_display = ("player_link", "best_left", "best_right", "get_player_categories")
    search_fields = ("player__name", "player__surname")
    readonly_fields = ("player_link", "best_left", "best_right", "get_player_categories")
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: BestSeeSawPressResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: BestSeeSawPressResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BestKBSquatResult)
class BestKBSquatResultAdmin(admin.ModelAdmin):
    list_display = ("player_link", "best_result", "get_player_categories")
    search_fields = ("player__name", "player__surname")
    readonly_fields = ("player_link", "best_result", "get_player_categories")
    list_select_related = ("player",)

    @admin.display(description=_("Player"), ordering="player__surname")
    def player_link(self, obj: BestKBSquatResult):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:live_results_player_change", args=[obj.player.id])
        return format_html('<a href="{}">{}</a>', link, obj.player)

    @admin.display(description=_("Categories"))
    def get_player_categories(self, obj: BestKBSquatResult) -> str:
        return ", ".join([c.name for c in obj.player.categories.all()])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

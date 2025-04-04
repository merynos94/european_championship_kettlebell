# admin.py
from django import forms
from django.contrib import admin
from django.db import models

# ===== POPRAWIONA LINIA PONIŻEJ =====
from django.db.models import F, Value  # Dodano import Value

# ====================================
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

# === Import Models ===
from .models import (
    # Constants
    AVAILABLE_DISCIPLINES,
    # Best Results (BestTGUResult, BestOneKettlebellPressResult usunięte z modeli)
    BestKBSquatResult,
    BestPistolSquatResult,
    BestSeeSawPressResult,
    BestSnatchResult,
    BestTwoKettlebellPressResult,
    # Entities
    Category,
    # Raw Results
    KBSquatResult,
    OneKettlebellPressResult,
    # Overall
    OverallResult,
    PistolSquatResult,
    # Player & Club
    Player,
    SeeSawPressResult,
    SnatchResult,
    SportClub,
    TGUResult,
    TwoKettlebellPressResult,
)

# === Import Resources ===
from .resources import PlayerExportResource, PlayerImportResource


# === Helper Functions ===
def player_link_display(obj, app_name="live_results"):
    """Generuje link HTML do strony zmiany gracza w adminie."""
    player = getattr(obj, "player", None)
    if player and player.pk:
        link = reverse(f"admin:{app_name}_player_change", args=[player.id])
        return format_html('<a href="{}">{}</a>', link, player)
    elif isinstance(obj, Player) and obj.pk:
        link = reverse(f"admin:{app_name}_player_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', link, obj)
    return _("Brak gracza")


def get_player_categories_display(obj) -> str:
    """Zwraca string z kategoriami gracza powiązanego z obiektem."""
    player = getattr(obj, "player", None)
    if player and player.pk and hasattr(player, "categories"):
        return ", ".join([c.name for c in player.categories.all()])
    elif isinstance(obj, Player) and hasattr(obj, "categories"):
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
        "get_categories_for_player",
        "get_best_snatch_display",
        "get_tgu_bw_percentage_display",
        "get_best_ssp_display",
        "get_best_kbs_display",
        "get_best_pistol_squat_display",
        "get_okbp_bw_percentage_display",
        "get_best_two_kb_press_display",
        "tiebreak",
    )
    list_filter = ("club", "categories", "tiebreak", ("weight", admin.EmptyFieldListFilter))
    search_fields = ("name", "surname", "club__name", "categories__name")

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
        (
            _("Najlepsze Wyniki Obliczone (Tylko do odczytu)"),
            {
                "classes": ("collapse",),
                "fields": (
                    "get_best_snatch_display",
                    "get_tgu_bw_percentage_display",
                    "get_best_ssp_display",
                    "get_best_kbs_display",
                    "get_best_pistol_squat_display",
                    "get_okbp_bw_percentage_display",
                    "get_best_two_kb_press_display",
                    "get_overall_score_display",
                ),
            },
        ),
    )

    readonly_fields = (
        "get_best_snatch_display",
        "get_tgu_bw_percentage_display",
        "get_best_ssp_display",
        "get_best_kbs_display",
        "get_best_pistol_squat_display",
        "get_okbp_bw_percentage_display",
        "get_best_two_kb_press_display",
        "get_overall_score_display",
    )

    # --- Metody Display dla PlayerAdmin ---
    @admin.display(description=_("Kategorie"))
    def get_categories_for_player(self, obj: Player) -> str:
        return get_player_categories_display(obj)

    @admin.display(description=_("Najlepszy Snatch"))
    def get_best_snatch_display(self, obj: Player) -> str:
        try:
            res = obj.best_snatch_result
            score = res.best_result
            return f"{score:.1f}" if score is not None else "---"
        except BestSnatchResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("TGU (%BW)"))
    def get_tgu_bw_percentage_display(self, obj: Player) -> str:
        try:
            result_obj = obj.tgu_result
            bw_perc = result_obj.bw_percentage
            return f"{bw_perc:.2f}%" if bw_perc is not None else "---"
        except TGUResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy SSP (%)"))
    def get_best_ssp_display(self, obj: Player) -> str:
        try:
            res = obj.best_see_saw_press_result
            return f"{res.best_result:.1f}%" if res.best_result is not None else "---"
        except BestSeeSawPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy KB Squat (Suma)"))
    def get_best_kbs_display(self, obj: Player) -> str:
        try:
            return f"{obj.best_kb_squat_result.best_result:.1f}"
        except BestKBSquatResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy Pistol Squat"))
    def get_best_pistol_squat_display(self, obj: Player) -> str:
        try:
            return f"{obj.best_pistol_squat_result.best_result:.1f}"
        except BestPistolSquatResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("One KB Press (%BW)"))
    def get_okbp_bw_percentage_display(self, obj: Player) -> str:
        try:
            result_obj = obj.one_kettlebell_press_result
            bw_perc = result_obj.bw_percentage
            return f"{bw_perc:.2f}%" if bw_perc is not None else "---"
        except OneKettlebellPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Najlepszy Two KB Press (Suma)"))
    def get_best_two_kb_press_display(self, obj: Player) -> str:
        try:
            return f"{obj.best_two_kettlebell_press_result.best_result:.1f}"
        except BestTwoKettlebellPressResult.DoesNotExist:
            return "---"
        except AttributeError:
            return "---"

    @admin.display(description=_("Wynik Ogólny"))
    def get_overall_score_display(self, obj: Player) -> str:
        try:
            # Sprawdź, czy overallresult istnieje, zanim odwołasz się do total_points
            overall = getattr(obj, "overallresult", None)
            if overall:
                return f"{overall.total_points:.1f}" if overall.total_points is not None else "---"
            return "---"  # Zwróć "---" jeśli overallresult nie istnieje
        except AttributeError:
            # Ten except może nie być już potrzebny po dodaniu getattr
            return "---"

    # Metody import/export
    def get_import_resource_classes(self, request):
        return [PlayerImportResource]

    def get_export_resource_classes(self, request):
        return [PlayerExportResource]

    # Metoda save_model dla debugowania
    def save_model(self, request, obj, form, change):
        # print(f"==== PlayerAdmin: WYWOŁANO save_model dla gracza {obj} ====")
        try:
            super().save_model(request, obj, form, change)
            # print(f"==== PlayerAdmin: super().save_model() ZAKOŃCZONE dla gracza {obj} ====")
        except Exception as e:
            print(f"!!!!!!!!!! PlayerAdmin: BŁĄD w super().save_model(): {e} !!!!!!!!!")
            import traceback

            traceback.print_exc()
            raise


# --- SportClub Admin ---
@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ("name", "player_count_display")
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(player_count_annotation=models.Count("players"))
        return qs

    @admin.display(description=_("Liczba Zawodników"), ordering="player_count_annotation")
    def player_count_display(self, obj: SportClub) -> int:
        return getattr(obj, "player_count_annotation", 0)


# --- Category Admin ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "get_disciplines_list_display")
    search_fields = ("name",)

    @admin.display(description=_("Dyscypliny"))
    def get_disciplines_list_display(self, obj: Category) -> str:
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
    list_select_related = ("player", "player__club")

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj):
        return player_link_display(obj)

    @admin.display(description=_("Max Wynik"), ordering="max_result_value")
    def get_max_result_display(self, obj) -> str:
        try:
            return f"{obj.max_result:.1f}"
        except AttributeError:
            return "N/A"

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str | None:
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
        # Poprawiona adnotacja z Value(0.0) - Value jest teraz zaimportowane
        qs = qs.annotate(max_result_value=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0)))
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
        "get_player_categories",
    )
    list_select_related = ("player", "player__club")

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj):
        return player_link_display(obj)

    @admin.display(description=_("Próba 1 (L/R)"))
    def get_attempt_1_display(self, obj) -> str:
        l = getattr(obj, "result_left_1", 0.0)
        r = getattr(obj, "result_right_1", 0.0)
        return f"{l or 0:.1f} / {r or 0:.1f}"

    @admin.display(description=_("Próba 2 (L/R)"))
    def get_attempt_2_display(self, obj) -> str:
        l = getattr(obj, "result_left_2", 0.0)
        r = getattr(obj, "result_right_2", 0.0)
        return f"{l or 0:.1f} / {r or 0:.1f}"

    @admin.display(description=_("Próba 3 (L/R)"))
    def get_attempt_3_display(self, obj) -> str:
        l = getattr(obj, "result_left_3", 0.0)
        r = getattr(obj, "result_right_3", 0.0)
        return f"{l or 0:.1f} / {r or 0:.1f}"

    @admin.display(description=_("Max Wynik (Suma)"), ordering="max_score_value")
    def get_max_score_display(self, obj) -> str:
        try:
            return f"{obj.max_score:.1f}"
        except AttributeError:
            # Awaryjne obliczenie, zakładając, że pola istnieją
            l1, r1 = getattr(obj, "result_left_1", 0.0), getattr(obj, "result_right_1", 0.0)
            l2, r2 = getattr(obj, "result_left_2", 0.0), getattr(obj, "result_right_2", 0.0)
            l3, r3 = getattr(obj, "result_left_3", 0.0), getattr(obj, "result_right_3", 0.0)
            score1 = (l1 or 0) + (r1 or 0) if l1 is not None and r1 is not None else 0
            score2 = (l2 or 0) + (r2 or 0) if l2 is not None and r2 is not None else 0
            score3 = (l3 or 0) + (r3 or 0) if l3 is not None and r3 is not None else 0
            return f"{max(score1, score2, score3):.1f}"

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str | None:
        try:
            bw = obj.bw_percentage
            return f"{bw:.2f}%" if bw is not None else "---"
        except AttributeError:
            return "N/A"

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str:
        return get_player_categories_display(obj)

    # Dodaj get_queryset do adnotacji max_score dla sortowania
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Dodano import Case na górze pliku
        from django.db.models import Case, FloatField, When  # Import lokalny, jeśli nie ma globalnie

        # Adnotacja dla max_score_value
        qs = qs.annotate(
            s_score_1=Case(
                When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")),
                default=Value(0.0),
                output_field=FloatField(),
            ),
            s_score_2=Case(
                When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")),
                default=Value(0.0),
                output_field=FloatField(),
            ),
            s_score_3=Case(
                When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")),
                default=Value(0.0),
                output_field=FloatField(),
            ),
        ).annotate(max_score_value=Greatest("s_score_1", "s_score_2", "s_score_3"))
        return qs


@admin.register(SnatchResult)
class SnatchResultAdmin(admin.ModelAdmin):
    list_display = ("player_link", "result", "position", "get_player_categories")
    list_filter = ("player__categories", "position")
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("player_link", "position", "get_player_categories")
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
        "get_max_score_display",
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
        "get_max_score_display",
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
        "get_bw_percentage_display",
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
    ordering = ("final_position", "total_points")

    readonly_fields = (
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
    list_select_related = ("player", "player__club")
    list_prefetch_related = ("player__categories",)

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: OverallResult):
        return player_link_display(obj)

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: OverallResult) -> str:
        return get_player_categories_display(obj)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

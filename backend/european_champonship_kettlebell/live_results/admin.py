# admin.py
from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Case, F, FloatField, Value, When
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

# === Import Models ===
# Zakładamy, że modele są w podkatalogu 'models' aplikacji 'live_results'
from .models.category import Category
from .models.sport_club import SportClub
from .models.player import Player
# Zakładamy, że __init__.py w models/results/ eksportuje te modele
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    OverallResult,
    PistolSquatResult,
    SeeSawPressResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)
# Importuj stałe dyscyplin
from .models.constants import AVAILABLE_DISCIPLINES

# === Import Resources ===
from .resources import PlayerExportResource, PlayerImportResource


# === Helper Functions ===
# Ta funkcja nadal jest potrzebna dla OverallResultAdmin
def player_link_display(obj, app_name="live_results"):
    player = getattr(obj, "player", None)
    player_instance = None

    if isinstance(obj, Player):
        player_instance = obj
    elif player and isinstance(player, Player):
        player_instance = player

    if player_instance and player_instance.pk:
        link = reverse(f"admin:{app_name}_player_change", args=[player_instance.id])
        return format_html('<a href="{}">{}</a>', link, player_instance)
    return _("Brak gracza")

def get_player_categories_display(obj) -> str:
    player = getattr(obj, "player", None)
    target_player = obj if isinstance(obj, Player) else player

    if target_player and hasattr(target_player, "categories") and target_player.categories.exists():
        return ", ".join([c.name for c in target_player.categories.all()])
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
        inst = self.instance
        if inst and inst.pk:
            initial_disciplines = getattr(inst, "disciplines", [])
            self.fields["disciplines"].initial = initial_disciplines if isinstance(initial_disciplines, list) else []
        else:
            self.fields["disciplines"].initial = []

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(instance, 'set_disciplines'):
             instance.set_disciplines(self.cleaned_data.get("disciplines", []))
        else:
             instance.disciplines = self.cleaned_data.get("disciplines", [])
        if commit:
            instance.save()
        return instance


# === Model Admins ===

@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    resource_classes = [PlayerImportResource]
    export_resource_classes = [PlayerExportResource]
    list_display = (
        "full_name", "weight", "club", "get_categories_for_player",
        "get_snatch_score_display", "get_tgu_bw_percentage_display",
        "get_ssp_bw_percentage_display", "get_kbs_bw_percentage_display",
        "get_pistol_bw_percentage_display", "get_okbp_bw_percentage_display",
        "get_tkbp_bw_percentage_display", "tiebreak", "get_overall_score_display",
    )
    list_filter = ("club", "categories", "tiebreak", ("weight", admin.EmptyFieldListFilter))
    search_fields = ("name", "surname", "club__name", "categories__name") # Potrzebne dla autocomplete
    list_select_related = ('club',)
    list_prefetch_related = ('categories', 'snatch_result', 'tgu_result',
                             'see_saw_press_result', 'kb_squat_result',
                             'pistol_squat_result', 'one_kettlebell_press_result',
                             'two_kettlebell_press_result', 'overallresult')
    fieldsets = (
        (_("Dane Podstawowe"), {"fields": ("name", "surname", "weight", "club", "categories", "tiebreak")}),
        (_("Wyniki Obliczone (Tylko do odczytu)"), {
            "classes": ("collapse",),
            "fields": (
                "get_snatch_score_display", "get_tgu_bw_percentage_display",
                "get_ssp_bw_percentage_display", "get_kbs_bw_percentage_display",
                "get_pistol_bw_percentage_display", "get_okbp_bw_percentage_display",
                "get_tkbp_bw_percentage_display", "get_overall_score_display",
            ),
        }),
    )
    readonly_fields = (
        "get_snatch_score_display", "get_tgu_bw_percentage_display",
        "get_ssp_bw_percentage_display", "get_kbs_bw_percentage_display",
        "get_pistol_bw_percentage_display", "get_okbp_bw_percentage_display",
        "get_tkbp_bw_percentage_display", "get_overall_score_display",
    )

    # Metody display dla PlayerAdmin pozostają bez zmian
    @admin.display(description=_("Kategorie"))
    def get_categories_for_player(self, obj: Player) -> str: return get_player_categories_display(obj)
    @admin.display(description=_("Snatch Score"), ordering="snatch_result__result")
    def get_snatch_score_display(self, obj: Player) -> str:
        res = getattr(obj, "snatch_result", None); score = getattr(res, "result", None)
        return f"{score:.1f}" if score is not None else "---"
    @admin.display(description=_("TGU (%BW)"))
    def get_tgu_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "tgu_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("SSP (%BW)"))
    def get_ssp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "see_saw_press_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("KBS (%BW)"))
    def get_kbs_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "kb_squat_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("Pistol (%BW)"))
    def get_pistol_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "pistol_squat_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("OKBP (%BW)"))
    def get_okbp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "one_kettlebell_press_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("TKBP (%BW)"))
    def get_tkbp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "two_kettlebell_press_result", None); bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("Wynik Ogólny"), ordering="overallresult__total_points")
    def get_overall_score_display(self, obj: Player) -> str:
        overall = getattr(obj, "overallresult", None); total = getattr(overall, "total_points", None)
        return f"{total:.1f}" if total is not None else "---"
    def get_import_resource_classes(self, request=None): return [PlayerImportResource]
    def get_export_resource_classes(self, request=None): return [PlayerExportResource]
    def save_model(self, request, obj, form, change): super().save_model(request, obj, form, change)

@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ("name", "player_count_display")
    search_fields = ("name",)
    def get_queryset(self, request): return super().get_queryset(request).annotate(player_count_annotation=models.Count("players"))
    @admin.display(description=_("Liczba Zawodników"), ordering="player_count_annotation")
    def player_count_display(self, obj: SportClub) -> int: return getattr(obj, "player_count_annotation", 0)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "get_disciplines_list_display")
    search_fields = ("name",)
    @admin.display(description=_("Dyscypliny"))
    def get_disciplines_list_display(self, obj: Category) -> str:
        disciplines = getattr(obj, "get_disciplines", getattr(obj, "disciplines", None))
        if callable(disciplines): disciplines = disciplines()
        return ", ".join(disciplines) if isinstance(disciplines, list) else "N/A"

# --- Base Admin for Single Attempt Results ---
class BaseSingleResultAdmin(admin.ModelAdmin):
    # Zmieniono 'player_link' na 'get_player_name'
    list_display = ('get_player_name', 'result_1', 'result_2', 'result_3',
                    'get_max_result_display', 'get_bw_percentage_display',
                    'position', 'get_player_categories')
    # Zmieniono link na kolumnę z nazwą gracza
    list_display_links = ('get_player_name',) # <--- ZMIANA TUTAJ
    list_filter = ("player__categories", "position", ("player__weight", admin.EmptyFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("position", "get_max_result_display", "get_bw_percentage_display", "get_player_categories")
    list_select_related = ("player", "player__club")
    fields = ('player', 'result_1', 'result_2', 'result_3', 'position',
              'get_max_result_display', 'get_bw_percentage_display', 'get_player_categories')
    autocomplete_fields = ('player',)

    # NOWA METODA: Wyświetla tylko nazwę, bez linku HTML
    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    # Stare metody display (get_max_result_display, etc.) bez zmian
    @admin.display(description=_("Max Wynik"))
    def get_max_result_display(self, obj) -> str:
        max_res = getattr(obj, "max_result", None); return f"{max_res:.1f}" if max_res is not None else "---"
    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str:
        bw = getattr(obj, "bw_percentage", None); return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str: return get_player_categories_display(obj)


# --- Base Admin for Double Attempt Results ---
class BaseDoubleResultAdmin(admin.ModelAdmin):
    # Zmieniono 'player_link' na 'get_player_name'
    list_display = ('get_player_name', 'get_attempt_1_score_display',
                    'get_attempt_2_score_display', 'get_attempt_3_score_display',
                    'get_max_score_display', 'get_bw_percentage_display',
                    'position', 'get_player_categories')
    # Zmieniono link na kolumnę z nazwą gracza
    list_display_links = ('get_player_name',) # <--- ZMIANA TUTAJ
    list_filter = ("player__categories", "position", ("player__weight", admin.EmptyFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("position", "get_max_score_display", "get_attempt_1_score_display",
                       "get_attempt_2_score_display", "get_attempt_3_score_display",
                       "get_bw_percentage_display", "get_player_categories")
    list_select_related = ("player", "player__club")
    fields = ('player', ('result_left_1', 'result_right_1'), ('result_left_2', 'result_right_2'),
              ('result_left_3', 'result_right_3'), 'position', 'get_max_score_display',
              'get_bw_percentage_display', 'get_player_categories', 'get_attempt_1_score_display',
              'get_attempt_2_score_display', 'get_attempt_3_score_display')
    autocomplete_fields = ('player',)

    # NOWA METODA: Wyświetla tylko nazwę, bez linku HTML
    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    # Stare metody display (get_attempt_score_display, etc.) bez zmian
    @admin.display(description=_("Wynik Próby 1"))
    def get_attempt_1_score_display(self, obj) -> str:
        score = obj.get_attempt_score(1); return f"{score:.1f}" if score is not None else "---"
    @admin.display(description=_("Wynik Próby 2"))
    def get_attempt_2_score_display(self, obj) -> str:
        score = obj.get_attempt_score(2); return f"{score:.1f}" if score is not None else "---"
    @admin.display(description=_("Wynik Próby 3"))
    def get_attempt_3_score_display(self, obj) -> str:
        score = obj.get_attempt_score(3); return f"{score:.1f}" if score is not None else "---"
    @admin.display(description=_("Max Wynik (Suma)"))
    def get_max_score_display(self, obj) -> str:
        max_s = getattr(obj, "max_score", None); return f"{max_s:.1f}" if max_s is not None else "---"
    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str:
        bw = getattr(obj, "bw_percentage", None); return f"{bw:.2f}%" if bw is not None else "---"
    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str: return get_player_categories_display(obj)


# --- Indywidualne Adminy Wyników ---
@admin.register(SnatchResult)
class SnatchResultAdmin(admin.ModelAdmin):
    # Zmieniono 'player_link' na 'get_player_name'
    list_display = ('get_player_name', "kettlebell_weight", "repetitions", "get_snatch_score_admin", "position", "get_player_categories")
    # Zmieniono link na kolumnę z nazwą gracza
    list_display_links = ('get_player_name',) # <--- ZMIANA TUTAJ
    list_filter = ("player__categories", "position", ("kettlebell_weight", admin.AllValuesFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("position", "get_player_categories", "get_snatch_score_admin")
    fields = ('player', 'kettlebell_weight', 'repetitions', 'position',
              'get_snatch_score_admin', 'get_player_categories')
    list_select_related = ("player", "player__club")
    autocomplete_fields = ('player',)

    # NOWA METODA: Wyświetla tylko nazwę, bez linku HTML
    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj: SnatchResult):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    # Stare metody display (get_player_categories, get_snatch_score_admin) bez zmian
    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: SnatchResult) -> str: return get_player_categories_display(obj)
    @admin.display(description=_("Wynik (obl.)"), ordering='calculated_snatch_score')
    def get_snatch_score_admin(self, obj: SnatchResult) -> str:
        score = getattr(obj, "result", None); return f"{score:.1f}" if score is not None else "---"
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(calculated_snatch_score=Case(
            When(kettlebell_weight__gt=0, repetitions__gt=0, then=F('kettlebell_weight') * F('repetitions')),
            default=Value(0.0), output_field=FloatField()
        ))
        return qs


# Klasy dziedziczące - teraz odziedziczą poprawny list_display_links i metodę get_player_name
@admin.register(TGUResult)
class TGUResultAdmin(BaseSingleResultAdmin): pass

@admin.register(OneKettlebellPressResult)
class OneKettlebellPressResultAdmin(BaseSingleResultAdmin): pass

@admin.register(PistolSquatResult)
class PistolSquatResultAdmin(BaseSingleResultAdmin): pass

@admin.register(SeeSawPressResult)
class SeeSawPressResultAdmin(BaseDoubleResultAdmin): pass

@admin.register(KBSquatResult)
class KBSquatResultAdmin(BaseDoubleResultAdmin): pass

@admin.register(TwoKettlebellPressResult)
class TwoKettlebellPressResultAdmin(BaseDoubleResultAdmin): pass


# admin.py
# ... (importy i inne klasy Admin bez zmian) ...

@admin.register(OverallResult)
class OverallResultAdmin(admin.ModelAdmin):
    list_display = (
        "player_link", # Używamy helpera, który tworzy link do gracza
        "get_player_categories", # Używamy helpera
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
    # Ustawiamy list_display_links na None, aby lista sama w sobie nie była klikalna
    # do edycji OverallResult (co nie ma sensu, bo jest obliczany)
    list_display_links = None
    ordering = ("final_position", "total_points") # Sortowanie wg pozycji, potem punktów

    # readonly_fields powinny pozostać, aby uniemożliwić ręczną edycję obliczonych pól
    # w widoku szczegółowym (jeśli ktoś miałby do niego dostęp)
    readonly_fields = (
        "player_link", "get_player_categories", "snatch_points",
        "tgu_points", "see_saw_press_points", "kb_squat_points",
        "pistol_squat_points", "one_kb_press_points", "two_kb_press_points",
        "tiebreak_points", "total_points", "final_position",
    )
    list_select_related = ("player", "player__club")
    list_prefetch_related = ("player__categories",)
    list_filter = ('player__categories', 'final_position')
    search_fields = ("player__name", "player__surname", "player__club__name")


    # Metody display pozostają, player_link nadal prowadzi do ZAWODNIKA
    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: OverallResult):
        # Ta metoda nadal generuje link do strony edycji gracza
        return player_link_display(obj.player) # Przekazujemy obiekt Player

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: OverallResult) -> str:
        return get_player_categories_display(obj.player)

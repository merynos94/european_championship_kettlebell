"""Admin panel for managing kettlebell competition results"""

import traceback

from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Case, F, FloatField, Value, When
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin

from .models.category import Category
from .models.constants import (
    AVAILABLE_DISCIPLINES,
    KB_SQUAT,
    ONE_KB_PRESS,
    PISTOL_SQUAT,
    SEE_SAW_PRESS,
    SNATCH,
    TGU,
    TWO_KB_PRESS,
)
from .models.player import Player
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
from .models.sport_club import SportClub
from .resources import PlayerExportResource, PlayerImportResource
from .services import update_discipline_positions, update_overall_results_for_category

"""Helper function to display player link in admin panel"""


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


"""Helper function to display player categories in admin panel"""


def get_player_categories_display(obj) -> str:
    player = getattr(obj, "player", None)
    target_player = obj if isinstance(obj, Player) else player
    if target_player and hasattr(target_player, "categories") and target_player.categories.exists():
        return ", ".join([c.name for c in target_player.categories.all()])
    return "---"


"""Helper function to display player categories in admin panel"""


class CategoryAdminForm(forms.ModelForm):
    disciplines = forms.MultipleChoiceField(
        choices=AVAILABLE_DISCIPLINES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Dyscypliny"),
        help_text=_("Wybierz dyscypliny dla tej kategorii."),
    )
    """Form for CategoryAdmin to manage disciplines in admin panel"""

    class Meta:
        model = Category
        fields = ["name", "disciplines"]

    """Form for PlayerAdmin to manage disciplines in admin panel"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = self.instance
        if inst and inst.pk:
            initial_disciplines = getattr(inst, "disciplines", [])
            self.fields["disciplines"].initial = initial_disciplines if isinstance(initial_disciplines, list) else []
        else:
            self.fields["disciplines"].initial = []

    """Form for PlayerAdmin to manage disciplines in admin panel"""

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(instance, "set_disciplines"):
            instance.set_disciplines(self.cleaned_data.get("disciplines", []))
        else:
            instance.disciplines = self.cleaned_data.get("disciplines", [])
        if commit:
            instance.save()
        return instance


@admin.register(Player)
class PlayerAdmin(ImportExportModelAdmin):
    resource_classes = [PlayerImportResource]
    export_resource_classes = [PlayerExportResource]
    list_display = (
        "full_name",
        "weight",
        "club",
        "get_categories_for_player",
        "get_snatch_score_display",
        "get_tgu_bw_percentage_display",
        "get_ssp_bw_percentage_display",
        "get_kbs_bw_percentage_display",
        "get_pistol_bw_percentage_display",
        "get_okbp_bw_percentage_display",
        "get_tkbp_bw_percentage_display",
        "tiebreak",
        "get_overall_score_display",
    )
    list_filter = ("club", "categories", "tiebreak", ("weight", admin.EmptyFieldListFilter))
    search_fields = ("name", "surname", "club__name", "categories__name")
    list_select_related = ("club",)
    list_prefetch_related = (
        "categories",
        "snatch_result",
        "tgu_result",
        "see_saw_press_result",
        "kb_squat_result",
        "pistol_squat_result",
        "one_kettlebell_press_result",
        "two_kettlebell_press_result",
        "overallresult",
    )
    ordering = ("-overallresult__total_points", "surname", "name")  # DODANO domyślne sortowanie

    DISCIPLINE_TO_FIELD_MAP = {
        SNATCH: "get_snatch_score_display",
        TGU: "get_tgu_bw_percentage_display",
        SEE_SAW_PRESS: "get_ssp_bw_percentage_display",
        KB_SQUAT: "get_kbs_bw_percentage_display",
        PISTOL_SQUAT: "get_pistol_bw_percentage_display",
        ONE_KB_PRESS: "get_okbp_bw_percentage_display",
        TWO_KB_PRESS: "get_tkbp_bw_percentage_display",
    }

    def get_allowed_disciplines(self, obj: Player | None) -> set:
        allowed_disciplines = set()
        if obj and obj.pk and hasattr(obj, "categories"):
            for category in obj.categories.all():
                disciplines_in_cat = category.get_disciplines()
                if disciplines_in_cat:
                    allowed_disciplines.update(disciplines_in_cat)
        return allowed_disciplines

    def get_fieldsets(self, request, obj: Player | None = None):
        allowed_disciplines = self.get_allowed_disciplines(obj)
        fieldsets = [
            (_("Dane Podstawowe"), {"fields": ("name", "surname", "weight", "club", "categories", "tiebreak")}),
        ]
        results_fields = []
        for discipline_code, field_name in self.DISCIPLINE_TO_FIELD_MAP.items():
            if discipline_code in allowed_disciplines:
                results_fields.append(field_name)
        if results_fields or True:
            results_fields.append("get_overall_score_display")
        if results_fields:
            fieldsets.append(
                (
                    _("Wyniki Obliczone (Tylko do odczytu)"),
                    {
                        "classes": ("collapse",),
                        "fields": tuple(results_fields),
                    },
                )
            )
        return fieldsets

    def get_readonly_fields(self, request, obj: Player | None = None):
        allowed_disciplines = self.get_allowed_disciplines(obj)
        readonly = []
        for discipline_code, field_name in self.DISCIPLINE_TO_FIELD_MAP.items():
            if discipline_code in allowed_disciplines:
                readonly.append(field_name)
        readonly.append("get_overall_score_display")
        return tuple(readonly)

    @admin.display(description=_("Kategorie"))
    def get_categories_for_player(self, obj: Player) -> str:
        return get_player_categories_display(obj)

    @admin.display(description=_("Snatch Score"), ordering="snatch_result__result")
    def get_snatch_score_display(self, obj: Player) -> str:
        res = getattr(obj, "snatch_result", None)
        score = getattr(res, "result", None)
        return f"{score:.1f}" if score is not None else "---"

    @admin.display(description=_("TGU (%BW)"))
    def get_tgu_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "tgu_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("SSP (%BW)"))
    def get_ssp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "see_saw_press_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("KBS (%BW)"))
    def get_kbs_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "kb_squat_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Pistol (%BW)"))
    def get_pistol_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "pistol_squat_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("OKBP (%BW)"))
    def get_okbp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "one_kettlebell_press_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("TKBP (%BW)"))
    def get_tkbp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "two_kettlebell_press_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Wynik Ogólny"), ordering="overallresult__total_points")
    def get_overall_score_display(self, obj: Player) -> str:
        overall = getattr(obj, "overallresult", None)
        total = getattr(overall, "total_points", None)
        return f"{total:.1f}" if total is not None else "---"

    def get_import_resource_classes(self, request=None):
        return [PlayerImportResource]

    def get_export_resource_classes(self, request=None):
        return [PlayerExportResource]

    def save_model(self, request, obj: Player, form, change):
        old_categories_pks = set()
        if change and obj.pk:
            try:
                old_obj = Player.objects.get(pk=obj.pk)
                old_categories_pks = set(old_obj.categories.values_list("pk", flat=True))
            except Player.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)
        current_categories_pks = set(obj.categories.values_list("pk", flat=True))
        newly_added_category_pks = current_categories_pks - old_categories_pks
        from .services import create_default_results_for_player_categories, update_overall_results_for_player

        if newly_added_category_pks:
            print(f"Gracz {obj.id}: Dodano kategorie {newly_added_category_pks}. Tworzę domyślne rekordy wyników...")
            try:
                created_any = create_default_results_for_player_categories(obj, newly_added_category_pks)
                if created_any:
                    print(f"Stworzono nowe domyślne rekordy wyników dla gracza {obj.id}.")
                else:
                    print(
                        f"Nie stworzono nowych domyślnych rekordów (prawdopodobnie już istniały) dla gracza {obj.id}."
                    )
            except Exception as e:
                print(f"BŁĄD podczas tworzenia domyślnych rekordów dla gracza {obj.id}: {e}")
                traceback.print_exc()
                self.message_user(
                    request, f"Wystąpił błąd podczas tworzenia domyślnych rekordów wyników: {e}", level="ERROR"
                )
        print(f"Gracz {obj.id}: Uruchamiam przeliczenie wyników ogólnych...")
        try:
            update_overall_results_for_player(obj)
            print(f"Zakończono przeliczanie wyników ogólnych dla gracza {obj.id}.")
        except Exception as e:
            print(f"BŁĄD podczas przeliczania wyników ogólnych dla gracza {obj.id}: {e}")
            traceback.print_exc()
            self.message_user(request, f"Wystąpił błąd podczas przeliczania wyników ogólnych: {e}", level="ERROR")


@admin.register(SportClub)
class SportClubAdmin(admin.ModelAdmin):
    list_display = ("name", "player_count_display")
    search_fields = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(player_count_annotation=models.Count("players"))

    @admin.display(description=_("Liczba Zawodników"), ordering="player_count_annotation")
    def player_count_display(self, obj: SportClub) -> int:
        return getattr(obj, "player_count_annotation", 0)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "get_disciplines_list_display")
    search_fields = ("name",)
    actions = ["export_results_as_html"]

    DISCIPLINE_RELATED_NAMES = {
        SNATCH: "snatch_result",
        TGU: "tgu_result",
        SEE_SAW_PRESS: "see_saw_press_result",
        KB_SQUAT: "kb_squat_result",
        PISTOL_SQUAT: "pistol_squat_result",
        ONE_KB_PRESS: "one_kettlebell_press_result",
        TWO_KB_PRESS: "two_kettlebell_press_result",
    }
    DISCIPLINE_EXPORT_CONFIG = {
        SNATCH: {
            "header": "Snatch (kg x reps / wynik)",
            "attributes": ["kettlebell_weight", "repetitions", "result"],
            "template_snippet": "admin/live_results/category/export_snippets/snatch.html",
        },
        TGU: {
            "header": "TGU (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html",
        },
        PISTOL_SQUAT: {
            "header": "Pistol (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html",
        },
        ONE_KB_PRESS: {
            "header": "OH Press (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html",
        },
        SEE_SAW_PRESS: {
            "header": "SeeSaw Press (max kg / %BW)",
            "attributes": ["max_score", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/double_attempt.html",
        },
        KB_SQUAT: {
            "header": "KB Squat (max kg / %BW)",
            "attributes": ["max_score", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/double_attempt.html",
        },
        TWO_KB_PRESS: {
            "header": "2KB Press (max kg / %BW)",
            "attributes": ["max_score", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/double_attempt.html",
        },
    }

    @admin.display(description=_("Dyscypliny"))
    def get_disciplines_list_display(self, obj: Category) -> str:
        disciplines = getattr(obj, "get_disciplines", getattr(obj, "disciplines", None))
        if callable(disciplines):
            disciplines = disciplines()
        if isinstance(disciplines, list):
            return ", ".join(disciplines) if disciplines else "---"
        return "N/A"

    def save_model(self, request, obj: Category, form, change):
        super().save_model(request, obj, form, change)
        print(f"Zapisano kategorię '{obj.name}'. Uruchamiam przeliczenie wyników...")
        try:
            update_discipline_positions(obj)
            update_overall_results_for_category(obj)
            print(f"Przeliczenie wyników dla kategorii '{obj.name}' zakończone.")
            self.message_user(
                request, f"Wyniki dla kategorii '{obj.name}' zostały pomyślnie przeliczone.", level="INFO"
            )
        except Exception as e:
            print(f"BŁĄD podczas przeliczania wyników dla kategorii '{obj.name}' po zapisie: {e}")
            traceback.print_exc()
            self.message_user(
                request, f"Wystąpił błąd podczas przeliczania wyników dla kategorii '{obj.name}': {e}", level="ERROR"
            )

    @admin.action(description=_("Eksportuj szczegółowe wyniki kategorii do HTML"))
    def export_results_as_html(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request, _("Proszę wybrać dokładnie jedną kategorię do eksportu wyników."), level="WARNING"
            )
            return

        category = queryset.first()
        disciplines_in_category = sorted(list(category.get_disciplines()))

        discipline_columns = []
        prefetch_related_list = ["player__club"]
        for code in disciplines_in_category:
            if code in self.DISCIPLINE_EXPORT_CONFIG and code in self.DISCIPLINE_RELATED_NAMES:
                config = self.DISCIPLINE_EXPORT_CONFIG[code]
                related_name = self.DISCIPLINE_RELATED_NAMES[code]
                discipline_columns.append(
                    {
                        "code": code,
                        "header": config["header"],
                        "attributes": config["attributes"],
                        "related_name": related_name,
                        "template_snippet": config.get("template_snippet"),
                    }
                )
                prefetch_related_list.append(f"player__{related_name}")
            else:
                print(f"OSTRZEŻENIE: Brak konfiguracji eksportu lub related_name dla dyscypliny '{code}'")

        overall_results = (
            OverallResult.objects.filter(player__categories=category)
            .select_related("player")
            .prefetch_related(*prefetch_related_list)
            .order_by("final_position")
        )

        if not overall_results.exists():
            self.message_user(
                request, _("Brak wyników do wyeksportowania dla kategorii: %s") % category.name, level="INFO"
            )
            return

        table_rows = []
        for overall in overall_results:
            player = overall.player
            row_data = {
                "position": overall.final_position,
                "player": player,
                "club_name": player.club.name if player.club else "brak klubu",
                "total_points": overall.total_points,
                "discipline_results": {},
            }
            for disc_info in discipline_columns:
                result_obj = getattr(player, disc_info["related_name"], None)
                row_data["discipline_results"][disc_info["code"]] = result_obj

            table_rows.append(row_data)

        context = {
            "category": category,
            "discipline_columns": discipline_columns,
            "table_rows": table_rows,
        }

        html_content = render_to_string("admin/live_results/category/results_export_detailed.html", context)

        response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
        return response


class BaseResultAdminMixin:
    discipline_code = None

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player" and self.discipline_code:
            try:
                allowed_category_pks = {
                    cat.pk for cat in Category.objects.all() if self.discipline_code in cat.get_disciplines()
                }

                if allowed_category_pks:
                    kwargs["queryset"] = (
                        Player.objects.filter(categories__pk__in=allowed_category_pks)
                        .distinct()
                        .order_by("surname", "name")
                    )
                    print(
                        f"Ograniczono queryset graczy dla {self.__class__.__name__} do {kwargs['queryset'].count()} rekordów."
                    )
                else:
                    kwargs["queryset"] = Player.objects.none()
                    print(
                        f"Brak kategorii dla dyscypliny {self.discipline_code}, queryset graczy pusty dla {self.__class__.__name__}."
                    )

            except Exception as e:
                print(f"BŁĄD podczas filtrowania graczy w formfield_for_foreignkey dla {self.__class__.__name__}: {e}")
                traceback.print_exc()
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BaseSingleResultAdmin(BaseResultAdminMixin, admin.ModelAdmin):
    list_display = (
        "get_player_name",
        "result_1",
        "result_2",
        "result_3",
        "get_max_result_display",
        "get_bw_percentage_display",
        "position",
        "get_player_categories",
    )
    list_display_links = ("get_player_name",)
    list_filter = ("player__categories", "position", ("player__weight", admin.EmptyFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("position", "get_max_result_display", "get_bw_percentage_display", "get_player_categories")
    list_select_related = ("player", "player__club")
    fields = (
        "player",
        "result_1",
        "result_2",
        "result_3",
        "position",
        "get_max_result_display",
        "get_bw_percentage_display",
        "get_player_categories",
    )
    autocomplete_fields = ("player",)

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    @admin.display(description=_("Max Wynik"))
    def get_max_result_display(self, obj) -> str:
        max_res = getattr(obj, "max_result", None)
        return f"{max_res:.1f}" if max_res is not None else "---"

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str:
        bw = getattr(obj, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str:
        return get_player_categories_display(obj)


class BaseDoubleResultAdmin(BaseResultAdminMixin, admin.ModelAdmin):
    list_display = (
        "get_player_name",
        "get_attempt_1_score_display",
        "get_attempt_2_score_display",
        "get_attempt_3_score_display",
        "get_max_score_display",
        "get_bw_percentage_display",
        "position",
        "get_player_categories",
    )
    list_display_links = ("get_player_name",)
    list_filter = ("player__categories", "position", ("player__weight", admin.EmptyFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = (
        "position",
        "get_max_score_display",
        "get_attempt_1_score_display",
        "get_attempt_2_score_display",
        "get_attempt_3_score_display",
        "get_bw_percentage_display",
        "get_player_categories",
    )
    list_select_related = ("player", "player__club")
    fields = (
        "player",
        ("result_left_1", "result_right_1"),
        ("result_left_2", "result_right_2"),
        ("result_left_3", "result_right_3"),
        "position",
        "get_max_score_display",
        "get_bw_percentage_display",
        "get_player_categories",
        "get_attempt_1_score_display",
        "get_attempt_2_score_display",
        "get_attempt_3_score_display",
    )
    autocomplete_fields = ("player",)

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    @admin.display(description=_("Wynik Próby 1"))
    def get_attempt_1_score_display(self, obj) -> str:
        score = obj.get_attempt_score(1)
        return f"{score:.1f}" if score is not None else "---"

    @admin.display(description=_("Wynik Próby 2"))
    def get_attempt_2_score_display(self, obj) -> str:
        score = obj.get_attempt_score(2)
        return f"{score:.1f}" if score is not None else "---"

    @admin.display(description=_("Wynik Próby 3"))
    def get_attempt_3_score_display(self, obj) -> str:
        score = obj.get_attempt_score(3)
        return f"{score:.1f}" if score is not None else "---"

    @admin.display(description=_("Max Wynik (Suma)"))
    def get_max_score_display(self, obj) -> str:
        max_s = getattr(obj, "max_score", None)
        return f"{max_s:.1f}" if max_s is not None else "---"

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str:
        bw = getattr(obj, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj) -> str:
        return get_player_categories_display(obj)


@admin.register(SnatchResult)
class SnatchResultAdmin(BaseResultAdminMixin, admin.ModelAdmin):
    discipline_code = SNATCH
    list_display = (
        "get_player_name",
        "kettlebell_weight",
        "repetitions",
        "get_snatch_score_admin",
        "position",
        "get_player_categories",
    )
    list_display_links = ("get_player_name",)
    list_filter = ("player__categories", "position", ("kettlebell_weight", admin.AllValuesFieldListFilter))
    search_fields = ("player__name", "player__surname", "player__club__name")
    readonly_fields = ("position", "get_player_categories", "get_snatch_score_admin")
    fields = (
        "player",
        "kettlebell_weight",
        "repetitions",
        "position",
        "get_snatch_score_admin",
        "get_player_categories",
    )
    list_select_related = ("player", "player__club")
    autocomplete_fields = ("player",)

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj: SnatchResult):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    @admin.display(description=_("Kategorie"))
    def get_player_categories(self, obj: SnatchResult) -> str:
        return get_player_categories_display(obj)

    @admin.display(description=_("Wynik (obl.)"), ordering="calculated_snatch_score")
    def get_snatch_score_admin(self, obj: SnatchResult) -> str:
        score = getattr(obj, "result", None)
        return f"{score:.1f}" if score is not None else "---"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            calculated_snatch_score=Case(
                When(kettlebell_weight__gt=0, repetitions__gt=0, then=F("kettlebell_weight") * F("repetitions")),
                default=Value(0.0),
                output_field=FloatField(),
            )
        )
        return qs


@admin.register(TGUResult)
class TGUResultAdmin(BaseSingleResultAdmin):
    discipline_code = TGU


@admin.register(OneKettlebellPressResult)
class OneKettlebellPressResultAdmin(BaseSingleResultAdmin):
    discipline_code = ONE_KB_PRESS


@admin.register(PistolSquatResult)
class PistolSquatResultAdmin(BaseSingleResultAdmin):
    discipline_code = PISTOL_SQUAT


@admin.register(SeeSawPressResult)
class SeeSawPressResultAdmin(BaseDoubleResultAdmin):
    discipline_code = SEE_SAW_PRESS


@admin.register(KBSquatResult)
class KBSquatResultAdmin(BaseDoubleResultAdmin):
    discipline_code = KB_SQUAT


@admin.register(TwoKettlebellPressResult)
class TwoKettlebellPressResultAdmin(BaseDoubleResultAdmin):
    discipline_code = TWO_KB_PRESS


@admin.register(OverallResult)
class OverallResultAdmin(admin.ModelAdmin):
    list_display = (
        "player_link",
        "get_player_categories_display",
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
    list_display_links = None
    ordering = ("final_position", "total_points")
    readonly_fields = (
        "player_link",
        "get_player_categories_display",
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
    list_filter = ("player__categories", "final_position")
    search_fields = ("player__name", "player__surname", "player__club__name")
    actions = ["export_overall_results_as_html"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # Tylko do odczytu

    # def has_delete_permission(self, request, obj=None):
    #     return False # Tylko do odczytu

    DISCIPLINE_POINTS_FIELDS = {
        SNATCH: "snatch_points",
        TGU: "tgu_points",
        SEE_SAW_PRESS: "see_saw_press_points",
        KB_SQUAT: "kb_squat_points",
        PISTOL_SQUAT: "pistol_squat_points",
        ONE_KB_PRESS: "one_kb_press_points",
        TWO_KB_PRESS: "two_kb_press_points",
    }
    ORDERED_DISCIPLINE_CODES = [code for code, name in AVAILABLE_DISCIPLINES]

    @admin.action(description=_("Eksportuj podsumowanie wyników do HTML"))
    def export_overall_results_as_html(self, request, queryset):
        results = (
            queryset.select_related("player", "player__club")
            .prefetch_related("player__categories")
            .order_by("final_position", "total_points")
        )

        if not results.exists():
            self.message_user(request, _("Brak wyników do wyeksportowania."), level="INFO")
            return

        discipline_columns = []
        for code in self.ORDERED_DISCIPLINE_CODES:
            if code in self.DISCIPLINE_POINTS_FIELDS:
                discipline_columns.append(
                    {
                        "code": code,
                        "name": dict(AVAILABLE_DISCIPLINES).get(code, code),
                        "field_name": self.DISCIPLINE_POINTS_FIELDS[code],
                    }
                )

        table_rows = []
        for result in results:
            table_rows.append(
                {
                    "result": result,
                    "categories_str": ", ".join([c.name for c in result.player.categories.all()])
                    if result.player.categories.exists()
                    else "---",
                }
            )

        context = {
            "title": _("Podsumowanie Wyników Ogólnych"),
            "results_with_cats": table_rows,
            "discipline_columns": discipline_columns,
        }

        html_content = render_to_string("admin/live_results/overallresult/overall_export.html", context)

        response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
        return response

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: OverallResult):
        return player_link_display(obj.player)

    @admin.display(description=_("Kategorie"))
    def get_player_categories_display(self, obj: OverallResult) -> str:
        return get_player_categories_display(obj.player)

"""Admin panel for managing kettlebell competition results"""
from django.contrib import messages

import traceback
from django.http import HttpResponseRedirect
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
    SNATCH,
    TGU,
    TWO_KB_PRESS,
)
from .models.player import Player
from .models.results import (
    KBSquatResult, # Updated import
    OneKettlebellPressResult,
    CategoryOverallResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult, # Updated import
)
from .models.sport_club import SportClub
from .resources import PlayerExportResource, PlayerImportResource
from .services import (
    create_default_results_for_player_categories,
    update_discipline_positions,
    update_overall_results_for_category,
    update_overall_results_for_player,
)


def player_link_display(obj, app_name="live_results"):
    """Helper function to display player link in admin panel"""
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
    """Helper function to display player categories in admin panel"""
    player = getattr(obj, "player", None)
    target_player = obj if isinstance(obj, Player) else player
    if target_player and hasattr(target_player, "categories") and target_player.categories.exists():
        return ", ".join([c.name for c in target_player.categories.all()])
    return "---"


class CategoryAdminForm(forms.ModelForm):
    """Django Form for the Category model used in the admin interface."""

    disciplines = forms.MultipleChoiceField(
        choices=AVAILABLE_DISCIPLINES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Dyscypliny"),
        help_text=_("Wybierz dyscypliny dla tej kategorii."),
    )

    class Meta:
        """Form for CategoryAdmin to manage disciplines in admin panel"""
        model = Category
        fields = ["name", "disciplines"]

    def __init__(self, *args, **kwargs):
        """Initializes the form, setting initial disciplines for existing instances."""
        super().__init__(*args, **kwargs)
        inst = self.instance
        if inst and inst.pk:
            initial_disciplines = getattr(inst, "disciplines", [])
            self.fields["disciplines"].initial = initial_disciplines if isinstance(initial_disciplines, list) else []
        else:
            self.fields["disciplines"].initial = []

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
        "display_surname_name",
        "weight",
        "club",
        "get_categories_for_player",
        "get_snatch_score_display",
        "get_tgu_bw_percentage_display",
        "get_kbs_bw_percentage_display", # Uses KBSquatResult
        "get_okbp_bw_percentage_display",
        "get_tkbp_bw_percentage_display", # Uses TwoKettlebellPressResult
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
        "kb_squat_one_result",
        "one_kettlebell_press_result",
        "two_kettlebell_press_one_result",
        "overallresult",
    )
    ordering = ("-overallresult__total_points", "surname", "name")

    DISCIPLINE_TO_FIELD_MAP = {
        SNATCH: "get_snatch_score_display",
        TGU: "get_tgu_bw_percentage_display",
        KB_SQUAT: "get_kbs_bw_percentage_display",
        ONE_KB_PRESS: "get_okbp_bw_percentage_display",
        TWO_KB_PRESS: "get_tkbp_bw_percentage_display",
    }

    @admin.display(description="Nazwisko, Imię", ordering="surname")
    def display_surname_name(self, obj):
        if obj.surname and obj.name:
            return f"{obj.surname} {obj.name}"
        elif obj.surname:
            return obj.surname
        elif obj.name:
            return obj.name
        else:
            return "---"

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
        # Use updated DISCIPLINE_TO_FIELD_MAP
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
        # Use updated DISCIPLINE_TO_FIELD_MAP
        for discipline_code, field_name in self.DISCIPLINE_TO_FIELD_MAP.items():
            if discipline_code in allowed_disciplines:
                readonly.append(field_name)
        readonly.append("get_overall_score_display")
        return tuple(readonly)

    @admin.display(description=_("Kategorie"))
    def get_categories_for_player(self, obj: Player) -> str:
        return get_player_categories_display(obj)

    @admin.display(description=_("Snatch Score"))
    def get_snatch_score_display(self, obj: Player) -> str:
        res = getattr(obj, "snatch_result", None)
        score = getattr(res, "result", None)
        return f"{score:.1f}" if score is not None else "---"

    @admin.display(description=_("TGU (%BW)"))
    def get_tgu_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "tgu_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    # @admin.display(description=_("SSP (%BW)")) # Commented out based on request
    # def get_ssp_bw_percentage_display(self, obj: Player) -> str:
    #     res = getattr(obj, "see_saw_press_result", None)
    #     bw = getattr(res, "bw_percentage", None)
    #     return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("KBS (%BW)"))
    def get_kbs_bw_percentage_display(self, obj: Player) -> str:
        # Updated related name based on new model [cite: 1]
        res = getattr(obj, "kb_squat_one_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    # @admin.display(description=_("Pistol (%BW)")) # Commented out based on request
    # def get_pistol_bw_percentage_display(self, obj: Player) -> str:
    #     res = getattr(obj, "pistol_squat_result", None)
    #     bw = getattr(res, "bw_percentage", None)
    #     return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("OKBP (%BW)"))
    def get_okbp_bw_percentage_display(self, obj: Player) -> str:
        res = getattr(obj, "one_kettlebell_press_result", None)
        bw = getattr(res, "bw_percentage", None)
        return f"{bw:.2f}%" if bw is not None else "---"

    @admin.display(description=_("TKBP (%BW)"))
    def get_tkbp_bw_percentage_display(self, obj: Player) -> str:
        # Updated related name based on new model [cite: 3]
        res = getattr(obj, "two_kettlebell_press_one_result", None)
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
        """Handles saving the Player model. Triggers a full results update after saving (e.g., for weight changes)."""
        super().save_model(request, obj, form, change)
        print(f"[Admin save_model] Saved player {obj.id}. Triggering overall results recalculation...")
        try:
            update_overall_results_for_player(obj)
            print(f"[Admin save_model] Finished recalculating overall results for player {obj.id}.")
        except Exception as e:
            print(f"[Admin save_model] ERROR during results recalculation for player {obj.id}: {e}")
            traceback.print_exc()
            self.message_user(request, f"An error occurred during results recalculation: {e}", level="ERROR")

    def save_related(self, request, form, formsets, change):
        """Called AFTER saving ManyToMany relationships (e.g., categories). Ideal place to create default records for NEW players."""
        super().save_related(request, form, formsets, change)

        if not change:
            player_instance = form.instance
            category_pks = set(player_instance.categories.values_list("pk", flat=True))

            if category_pks:
                print(
                    f"[Admin save_related] New player {player_instance.id} has categories {category_pks}. Creating default result records..."
                )
                try:
                    created_any = create_default_results_for_player_categories(player_instance, category_pks)
                    if created_any:
                        print(
                            f"[Admin save_related] Created new default result records for player {player_instance.id}.")
                    else:
                        print(
                            f"[Admin save_related] No new default records created (likely already existed?) for player {player_instance.id}."
                        )

                    print(f"[Admin save_related] Triggering full results update for new player {player_instance.id}...")
                    update_overall_results_for_player(player_instance)
                    print(f"[Admin save_related] Finished update for new player {player_instance.id}.")

                except Exception as e:
                    print(f"[Admin save_related] CRITICAL ERROR while handling new player {player_instance.id}: {e}")
                    traceback.print_exc()
                    self.message_user(
                        request,
                        f"An error occurred while creating/updating results for the new player: {e}",
                        level="ERROR",
                    )
            else:
                print(
                    f"[Admin save_related] New player {player_instance.id} has no assigned categories. Skipping default results creation."
                )


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

    # Updated DISCIPLINE_RELATED_NAMES based on comments and changes
    DISCIPLINE_RELATED_NAMES = {
        SNATCH: "snatch_result",
        TGU: "tgu_result",
        # SEE_SAW_PRESS: "see_saw_press_result", # Commented out
        KB_SQUAT: "kb_squat_one_result", # Changed related name [cite: 1]
        # PISTOL_SQUAT: "pistol_squat_result", # Commented out
        ONE_KB_PRESS: "one_kettlebell_press_result",
        TWO_KB_PRESS: "two_kettlebell_press_one_result", # Changed related name [cite: 3]
    }
    # Updated DISCIPLINE_EXPORT_CONFIG based on comments and changes
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
        # PISTOL_SQUAT: { # Commented out
        #     "header": "Pistol (max kg / %BW)",
        #     "attributes": ["max_result", "bw_percentage", "position"],
        #     "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html",
        # },
        ONE_KB_PRESS: {
            "header": "OH Press (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"],
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html",
        },
        # SEE_SAW_PRESS: { # Commented out
        #     "header": "SeeSaw Press (max kg / %BW)",
        #     "attributes": ["max_score", "bw_percentage", "position"],
        #     "template_snippet": "admin/live_results/category/export_snippets/double_attempt.html",
        # },
        KB_SQUAT: { # Changed base class implies single attempt logic
            "header": "KB Squat (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"], # Changed attributes
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html", # Changed template
        },
        TWO_KB_PRESS: { # Changed base class implies single attempt logic
            "header": "2KB Press (max kg / %BW)",
            "attributes": ["max_result", "bw_percentage", "position"], # Changed attributes
            "template_snippet": "admin/live_results/category/export_snippets/single_attempt.html", # Changed template
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
        print(f"Saved category '{obj.name}'. Triggering results recalculation...")
        try:
            update_discipline_positions(obj)
            update_overall_results_for_category(obj)
            print(f"Results recalculation for category '{obj.name}' finished.")
            self.message_user(
                request, f"Results for category '{obj.name}' have been successfully recalculated.", level="INFO"
            )
        except Exception as e:
            print(f"ERROR during results recalculation for category '{obj.name}' after save: {e}")
            traceback.print_exc()
            self.message_user(
                request, f"An error occurred while recalculating results for category '{obj.name}': {e}", level="ERROR"
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
        # Use updated DISCIPLINE_RELATED_NAMES
        prefetch_related_list = ["player__club"]
        for code in disciplines_in_category:
            # Use updated DISCIPLINE_EXPORT_CONFIG and DISCIPLINE_RELATED_NAMES
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
                print(f"WARNING: Missing export configuration or related_name for discipline '{code}'")

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
                        f"Restricted player queryset for {self.__class__.__name__} to {kwargs['queryset'].count()} records."
                    )
                else:
                    kwargs["queryset"] = Player.objects.none()
                    print(
                        f"No categories for discipline {self.discipline_code}, player queryset empty for {self.__class__.__name__}."
                    )

            except Exception as e:
                print(f"ERROR while filtering players in formfield_for_foreignkey for {self.__class__.__name__}: {e}")
                traceback.print_exc()
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BaseSingleResultAdmin(BaseResultAdminMixin, admin.ModelAdmin):
    # Displaying result_1, result_2, result_3 - assuming they exist on the model
    list_display = (
        "get_player_name",
        "result_1", # Should exist on BaseSingleAttemptResult model
        "result_2", # Should exist on BaseSingleAttemptResult model
        "result_3", # Should exist on BaseSingleAttemptResult model
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
        "result_1", # Should exist on BaseSingleAttemptResult model
        "result_2", # Should exist on BaseSingleAttemptResult model
        "result_3", # Should exist on BaseSingleAttemptResult model
        "position",
        "get_max_result_display",
        "get_bw_percentage_display",
        "get_player_categories",
    )
    autocomplete_fields = ("player",)
    ordering = ('position', 'player__surname', 'player__name')

    def response_change(self, request, obj):
        """
        Called after saving changes to an existing object.
        If the standard 'Save' button was pressed, redirect to the clean
        changelist view without preserving filters or ordering.
        Otherwise, fall back to default Django admin behavior.
        """
        if "_save" in request.POST:
            list_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
            messages.success(request, _("Zmiany w %(name)s zostały zapisane pomyślnie.") % {'name': str(obj)})
            return HttpResponseRedirect(list_url)
        else:
            return super().response_change(request, obj)
    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def get_player_name(self, obj):
        player = getattr(obj, "player", None)
        return str(player) if player else _("Brak Gracza")

    @admin.display(description=_("Max Wynik"))
    def get_max_result_display(self, obj) -> str:
        # Assuming 'max_result' property exists on BaseSingleAttemptResult model
        max_res = getattr(obj, "max_result", None)
        return f"{max_res:.1f}" if max_res is not None else "---"

    @admin.display(description=_("% Masy Ciała"))
    def get_bw_percentage_display(self, obj) -> str:
        # Assuming 'bw_percentage' property exists on BaseSingleAttemptResult model
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
    ordering = ('position', 'player__surname', 'player__name')

    def response_change(self, request, obj):
        """
        Called after saving changes to an existing object.
        If the standard 'Save' button was pressed, redirect to the clean
        changelist view without preserving filters or ordering.
        Otherwise, fall back to default Django admin behavior.
        """
        if "_save" in request.POST:
            list_url = reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')
            messages.success(request, _("Zmiany w %(name)s zostały zapisane pomyślnie.") % {'name': str(obj)})
            return HttpResponseRedirect(list_url)
        else:
            return super().response_change(request, obj)

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


# Updated admin registration to use BaseSingleResultAdmin based on new model [cite: 1]
@admin.register(KBSquatResult)
class KBSquatResultAdmin(BaseSingleResultAdmin):
    discipline_code = KB_SQUAT


# Inherits from BaseSingleResultAdmin, should work if BaseSingleAttemptResult has result_1,2,3
@admin.register(TwoKettlebellPressResult)
class TwoKettlebellPressResultAdmin(BaseSingleResultAdmin):
    discipline_code = TWO_KB_PRESS



@admin.register(CategoryOverallResult)
class OverallResultAdmin(admin.ModelAdmin):
    # (Keep the list_display, ordering, readonly_fields, etc. as they were in the previous corrected version)
    list_display = (
        "player_link",
        "get_player_categories_display",
        "snatch_points",
        "tgu_points",
        "kb_squat_points",
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
        "kb_squat_points",
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
        return False


    # Define the points mapping first
    DISCIPLINE_POINTS_FIELDS = {
        SNATCH: "snatch_points",
        TGU: "tgu_points",
        KB_SQUAT: "kb_squat_points",
        ONE_KB_PRESS: "one_kb_press_points",
        TWO_KB_PRESS: "two_kb_press_points",
    }

    # Define ordered codes based ONLY on the imported constant
    # We will filter this list inside the method below
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
        # Filter the codes *inside* the method using the defined points fields
        for code in self.ORDERED_DISCIPLINE_CODES:
            if code in self.DISCIPLINE_POINTS_FIELDS: # Filter using the class attribute
                discipline_columns.append(
                    {
                        "code": code,
                        "name": dict(AVAILABLE_DISCIPLINES).get(code, code),
                        "field_name": self.DISCIPLINE_POINTS_FIELDS[code], # Access via self
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
            "discipline_columns": discipline_columns, # Use the filtered list
        }

        html_content = render_to_string("admin/live_results/overallresult/overall_export.html", context)

        response = HttpResponse(html_content, content_type="text/html; charset=utf-8")
        return response

    @admin.display(description=_("Zawodnik"), ordering="player__surname")
    def player_link(self, obj: CategoryOverallResult):
        return player_link_display(obj.player)

    @admin.display(description=_("Kategorie"))
    def get_player_categories_display(self, obj: CategoryOverallResult) -> str:
        return get_player_categories_display(obj.player)


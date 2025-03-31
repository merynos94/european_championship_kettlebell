# -*- coding: utf-8 -*-
"""Service functions for business logic related to models."""

from typing import TYPE_CHECKING
from django.db import models
from django.db.models import F, Case, When, Value, FloatField
from django.db.models.functions import Greatest
from django.utils.translation import gettext_lazy as _

# Importuj stałe
from .constants import SNATCH, TGU, SEE_SAW_PRESS, KB_SQUAT, PISTOL_SQUAT

# Importuj modele używając TYPE_CHECKING dla podpowiedzi typów
if TYPE_CHECKING:
    from .category import Category
    from .player import Player
    from .results.snatch import SnatchResult
    from .results.tgu import TGUResult
    from .results.pistol_squat import PistolSquatResult
    from .results.see_saw_press import SeeSawPressResult
    from .results.kb_squat import KBSquatResult
    from .results.overall import OverallResult


def update_discipline_positions(category: 'Category') -> None:
    """
    Calculates and updates the position for each player within a category
    for every active discipline in that category.
    """
    # Importuj modele tutaj, aby uniknąć problemów z importem kołowym na starcie
    from .player import Player
    from .results.snatch import SnatchResult
    from .results.tgu import TGUResult
    from .results.pistol_squat import PistolSquatResult
    from .results.see_saw_press import SeeSawPressResult
    from .results.kb_squat import KBSquatResult

    players_in_category = Player.objects.filter(categories=category)
    disciplines = category.get_disciplines()

    discipline_models_map = {
        SNATCH: SnatchResult,
        TGU: TGUResult,
        SEE_SAW_PRESS: SeeSawPressResult,
        KB_SQUAT: KBSquatResult,
        PISTOL_SQUAT: PistolSquatResult,
    }

    # Define scoring fields/annotations for ordering
    ordering_logic = {
        SNATCH: '-result',
        TGU: '-max_tgu_result', # Użyjemy adnotacji
        PISTOL_SQUAT: '-max_pistol_result', # Użyjemy adnotacji
        SEE_SAW_PRESS: '-max_ssp_score', # Użyjemy adnotacji
        KB_SQUAT: '-max_kbs_score', # Użyjemy adnotacji
    }

    for discipline in disciplines:
        if discipline not in discipline_models_map:
            continue # Pomiń nieznane dyscypliny

        model = discipline_models_map[discipline]
        order_by_field = ordering_logic[discipline]

        # Base queryset for the discipline results of players in the category
        results_qs = model.objects.filter(player__in=players_in_category)

        # Add annotations for disciplines needing calculated max scores
        if discipline == TGU:
            results_qs = results_qs.annotate(
                max_tgu_result=Greatest('result_1', 'result_2', 'result_3')
            )
        elif discipline == PISTOL_SQUAT:
             results_qs = results_qs.annotate(
                max_pistol_result=Greatest('result_1', 'result_2', 'result_3')
            )
        elif discipline == SEE_SAW_PRESS:
            results_qs = results_qs.annotate(
                ssp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F('result_left_1') + F('result_right_1')), default=Value(0.0), output_field=FloatField()),
                ssp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F('result_left_2') + F('result_right_2')), default=Value(0.0), output_field=FloatField()),
                ssp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F('result_left_3') + F('result_right_3')), default=Value(0.0), output_field=FloatField()),
            ).annotate(max_ssp_score=Greatest('ssp_score_1', 'ssp_score_2', 'ssp_score_3'))
        elif discipline == KB_SQUAT:
             results_qs = results_qs.annotate(
                kbs_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F('result_left_1') + F('result_right_1')), default=Value(0.0), output_field=FloatField()),
                kbs_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F('result_left_2') + F('result_right_2')), default=Value(0.0), output_field=FloatField()),
                kbs_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F('result_left_3') + F('result_right_3')), default=Value(0.0), output_field=FloatField()),
            ).annotate(max_kbs_score=Greatest('kbs_score_1', 'kbs_score_2', 'kbs_score_3'))


        # Order the results
        ordered_results = results_qs.order_by(order_by_field, 'player__surname', 'player__name') # Dodatkowe sortowanie dla remisów

        # Update positions - Use bulk_update for efficiency
        updates = []
        current_pos = 0
        last_score = None
        rank_counter = 0
        for result in ordered_results:
            rank_counter += 1
            # Determine score based on discipline
            if discipline == SNATCH: score = result.result
            elif discipline == TGU: score = result.max_tgu_result
            elif discipline == PISTOL_SQUAT: score = result.max_pistol_result
            elif discipline == SEE_SAW_PRESS: score = result.max_ssp_score
            elif discipline == KB_SQUAT: score = result.max_kbs_score
            else: score = None # Should not happen

            # Handle ties - assign same position for ties
            if score != last_score:
                current_pos = rank_counter
                last_score = score

            if result.position != current_pos:
                result.position = current_pos
                updates.append(result)

        if updates:
            model.objects.bulk_update(updates, ['position'])


def update_overall_results_for_category(category: 'Category') -> None:
    """
    Calculates and updates overall scores and final positions for all players
    within a specific category based on their discipline positions.
    """
    # Importuj modele tutaj
    from .player import Player
    from .results.overall import OverallResult
    from .results.snatch import SnatchResult
    from .results.tgu import TGUResult
    from .results.pistol_squat import PistolSquatResult
    from .results.see_saw_press import SeeSawPressResult
    from .results.kb_squat import KBSquatResult

    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        'snatch_result', 'tgu_result', 'pistol_squat_result',
        'see_saw_press_result', 'kb_squat_result' # Prefetch related results
    )
    disciplines = category.get_disciplines()

    overall_updates = []

    # 1. Calculate points based on position in each active discipline
    for player in players_in_category:
        overall_result, created = OverallResult.objects.get_or_create(player=player)

        # Reset points
        overall_result.snatch_points = 0.0
        overall_result.tgu_points = 0.0
        overall_result.see_saw_press_points = 0.0
        overall_result.kb_squat_points = 0.0
        overall_result.pistol_squat_points = 0.0
        overall_result.tiebreak_points = -0.5 if player.tiebreak else 0.0 # Tiebreak points

        # Assign points based on position (lower position = lower points/rank)
        if SNATCH in disciplines and hasattr(player, 'snatch_result') and player.snatch_result.position is not None:
            overall_result.snatch_points = float(player.snatch_result.position)
        if TGU in disciplines and hasattr(player, 'tgu_result') and player.tgu_result.position is not None:
            overall_result.tgu_points = float(player.tgu_result.position)
        if SEE_SAW_PRESS in disciplines and hasattr(player, 'see_saw_press_result') and player.see_saw_press_result.position is not None:
            overall_result.see_saw_press_points = float(player.see_saw_press_result.position)
        if KB_SQUAT in disciplines and hasattr(player, 'kb_squat_result') and player.kb_squat_result.position is not None:
            overall_result.kb_squat_points = float(player.kb_squat_result.position)
        if PISTOL_SQUAT in disciplines and hasattr(player, 'pistol_squat_result') and player.pistol_squat_result.position is not None:
            overall_result.pistol_squat_points = float(player.pistol_squat_result.position)

        # Calculate total points (lower is better)
        overall_result.calculate_total_points() # Method on OverallResult model sums the points
        overall_updates.append(overall_result)

    # Bulk update points before calculating final position
    if overall_updates:
        OverallResult.objects.bulk_update(
            overall_updates,
            ['snatch_points', 'tgu_points', 'see_saw_press_points', 'kb_squat_points',
             'pistol_squat_points', 'tiebreak_points', 'total_points']
        )

    # 2. Determine final positions based on total points (lower is better)
    final_results = OverallResult.objects.filter(player__in=players_in_category).order_by(
        'total_points', 'player__surname', 'player__name' # Sort by points, then name for tie-breaking rank
    )

    final_pos_updates = []
    current_final_pos = 0
    last_total_points = None
    rank_counter = 0
    for result in final_results:
        rank_counter += 1
        if result.total_points != last_total_points:
            current_final_pos = rank_counter
            last_total_points = result.total_points

        if result.final_position != current_final_pos:
            result.final_position = current_final_pos
            final_pos_updates.append(result)

    if final_pos_updates:
        OverallResult.objects.bulk_update(final_pos_updates, ['final_position'])


def update_overall_results_for_player(player: 'Player') -> None:
    """Updates overall results for all categories the player belongs to."""
    # Należy zaktualizować pozycje we wszystkich kategoriach gracza
    # i przeliczyć wyniki ogólne dla tych kategorii.
    for category in player.categories.all():
         # Najpierw zaktualizuj pozycje w dyscyplinach dla całej kategorii
         update_discipline_positions(category)
         # Następnie zaktualizuj wyniki ogólne dla całej kategorii
         update_overall_results_for_category(category)
# services.py
from typing import TYPE_CHECKING

from django.db.models import Case, F, FloatField, Value, When
from django.db.models.functions import Greatest

from .constants import KB_SQUAT, ONE_KB_PRESS, PISTOL_SQUAT, SEE_SAW_PRESS, SNATCH, TGU, TWO_KB_PRESS
from .results.kb_squat import KBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult
from .results.snatch import SnatchResult
from .results.tgu import TGUResult
from .results.two_kettlebell_press import TwoKettlebellPressResult

if TYPE_CHECKING:
    from .category import Category
    from .player import Player


def update_discipline_positions(category: "Category") -> None:
    """
    Calculates and updates the position for each player within a category
    for every active discipline in that category.
    All disciplines except Snatch are ranked based on score / body_weight.
    """
    from .player import Player
    from .results.overall import OverallResult

    players_in_category = Player.objects.filter(categories=category)
    if not players_in_category.exists(): return
    disciplines = category.get_disciplines()
    if not disciplines: return

    discipline_models_map = {
        SNATCH: SnatchResult, TGU: TGUResult, SEE_SAW_PRESS: SeeSawPressResult,
        KB_SQUAT: KBSquatResult, PISTOL_SQUAT: PistolSquatResult,
        ONE_KB_PRESS: OneKettlebellPressResult, TWO_KB_PRESS: TwoKettlebellPressResult,
    }

    ordering_logic = {
        SNATCH: "-result", # Snatch wg wyniku - bez zmian
        TGU: "-tgu_bw_ratio", PISTOL_SQUAT: "-pistol_bw_ratio",
        ONE_KB_PRESS: "-okbp_bw_ratio", SEE_SAW_PRESS: "-ssp_bw_ratio",
        KB_SQUAT: "-kbs_bw_ratio", TWO_KB_PRESS: "-tkbp_bw_ratio",
    }

    for discipline in disciplines:
        if discipline not in discipline_models_map: continue
        model = discipline_models_map[discipline]
        order_by_field = ordering_logic.get(discipline)
        if not order_by_field: continue

        results_qs = model.objects.select_related("player").filter(player__in=players_in_category)

        if discipline == TGU:
             results_qs = results_qs.annotate(max_tgu_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0))).annotate(tgu_bw_ratio=Case(When(player__weight__gt=0, max_tgu_result__gt=0, then=F("max_tgu_result")/F("player__weight")), default=Value(0.0), output_field=FloatField()))
        elif discipline == PISTOL_SQUAT:
            results_qs = results_qs.annotate(max_pistol_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0))).annotate(pistol_bw_ratio=Case(When(player__weight__gt=0, max_pistol_result__gt=0, then=F("max_pistol_result")/F("player__weight")), default=Value(0.0), output_field=FloatField()))
        elif discipline == ONE_KB_PRESS:
            results_qs = results_qs.annotate(max_okbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0))).annotate(okbp_bw_ratio=Case(When(player__weight__gt=0, max_okbp_result__gt=0, then=F("max_okbp_result")/F("player__weight")), default=Value(0.0), output_field=FloatField()))
        elif discipline == SEE_SAW_PRESS:
            results_qs = results_qs.annotate(ssp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1")+F("result_right_1")), default=Value(0.0), output_field=FloatField()), ssp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2")+F("result_right_2")), default=Value(0.0), output_field=FloatField()), ssp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3")+F("result_right_3")), default=Value(0.0), output_field=FloatField()),).annotate(max_ssp_score=Greatest("ssp_score_1", "ssp_score_2", "ssp_score_3")).annotate(ssp_bw_ratio=Case(When(player__weight__gt=0, max_ssp_score__gt=0, then=F("max_ssp_score")/F("player__weight")), default=Value(0.0), output_field=FloatField()))
        elif discipline == KB_SQUAT:
            results_qs = results_qs.annotate(kbs_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1")+F("result_right_1")), default=Value(0.0), output_field=FloatField()), kbs_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2")+F("result_right_2")), default=Value(0.0), output_field=FloatField()), kbs_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3")+F("result_right_3")), default=Value(0.0), output_field=FloatField()),).annotate(max_kbs_score=Greatest("kbs_score_1", "kbs_score_2", "kbs_score_3")).annotate(kbs_bw_ratio=Case(When(player__weight__gt=0, max_kbs_score__gt=0, then=F("max_kbs_score")/F("player__weight")), default=Value(0.0), output_field=FloatField()))
        elif discipline == TWO_KB_PRESS:
            results_qs = results_qs.annotate(tkbp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1")+F("result_right_1")), default=Value(0.0), output_field=FloatField()), tkbp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2")+F("result_right_2")), default=Value(0.0), output_field=FloatField()), tkbp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3")+F("result_right_3")), default=Value(0.0), output_field=FloatField()),).annotate(max_tkbp_score=Greatest("tkbp_score_1", "tkbp_score_2", "tkbp_score_3")).annotate(tkbp_bw_ratio=Case(When(player__weight__gt=0, max_tkbp_score__gt=0, then=F("max_tkbp_score")/F("player__weight")), default=Value(0.0), output_field=FloatField()))

        # Sortowanie
        ordered_results = results_qs.order_by(order_by_field, "player__surname", "player__name")

        updates = []; current_pos = 0; last_score = None; rank_counter = 0; epsilon = 1e-6
        for result in ordered_results:
            rank_counter += 1; score = 0.0
            try: # Pobierz wynik/ratio
                if discipline == SNATCH: score = result.result or 0.0 # Snatch używa 'result'
                elif discipline == TGU: score = result.tgu_bw_ratio or 0.0
                elif discipline == PISTOL_SQUAT: score = result.pistol_bw_ratio or 0.0
                elif discipline == ONE_KB_PRESS: score = result.okbp_bw_ratio or 0.0
                elif discipline == SEE_SAW_PRESS: score = result.ssp_bw_ratio or 0.0
                elif discipline == KB_SQUAT: score = result.kbs_bw_ratio or 0.0
                elif discipline == TWO_KB_PRESS: score = result.tkbp_bw_ratio or 0.0
            except AttributeError: pass

            last_score_for_comparison = last_score if last_score is not None else -1.0
            if abs(score - last_score_for_comparison) > epsilon:
                current_pos = rank_counter; last_score = score
            if result.position != current_pos:
                result.position = current_pos; updates.append(result)

        if updates:
            try: model.objects.bulk_update(updates, ["position"])
            except Exception as e_bulk: print(f"BŁĄD bulk_update dla {discipline}: {e_bulk}")


def update_overall_results_for_category(category: "Category") -> None:
    # Bez zmian
    from .player import Player
    from .results.overall import OverallResult
    players_in_category = Player.objects.filter(categories=category).prefetch_related( "snatch_result", "tgu_result", "pistol_squat_result", "see_saw_press_result", "kb_squat_result", "one_kettlebell_press_result", "two_kettlebell_press_result")
    disciplines = category.get_disciplines(); overall_updates = []
    for player in players_in_category:
        overall_result, created = OverallResult.objects.get_or_create(player=player)
        overall_result.snatch_points=None; overall_result.tgu_points=None; overall_result.see_saw_press_points=None; overall_result.kb_squat_points=None
        overall_result.pistol_squat_points=None; overall_result.one_kb_press_points=None; overall_result.two_kb_press_points=None
        overall_result.tiebreak_points = -0.5 if player.tiebreak else 0.0
        def get_points(discipline_name, result_attr_name):
            if discipline_name in disciplines:
                result_obj = getattr(player, result_attr_name, None)
                if result_obj and result_obj.position is not None: return float(result_obj.position)
            return None
        overall_result.snatch_points=get_points(SNATCH, "snatch_result"); overall_result.tgu_points=get_points(TGU, "tgu_result")
        overall_result.see_saw_press_points=get_points(SEE_SAW_PRESS, "see_saw_press_result"); overall_result.kb_squat_points=get_points(KB_SQUAT, "kb_squat_result")
        overall_result.pistol_squat_points=get_points(PISTOL_SQUAT, "pistol_squat_result"); overall_result.one_kb_press_points=get_points(ONE_KB_PRESS, "one_kettlebell_press_result")
        overall_result.two_kb_press_points=get_points(TWO_KB_PRESS, "two_kettlebell_press_result")
        overall_result.calculate_total_points(); overall_updates.append(overall_result)
    if overall_updates:
        update_fields = [ "snatch_points", "tgu_points", "see_saw_press_points", "kb_squat_points", "pistol_squat_points", "one_kb_press_points", "two_kb_press_points", "tiebreak_points", "total_points"]
        OverallResult.objects.bulk_update(overall_updates, update_fields)
    final_results = OverallResult.objects.filter(player__in=players_in_category).order_by("total_points", "player__surname", "player__name")
    final_pos_updates = []; current_final_pos = 0; last_total_points = None; rank_counter = 0
    for result in final_results:
        rank_counter += 1
        if last_total_points is None or result.total_points != last_total_points:
            current_final_pos = rank_counter; last_total_points = result.total_points
        if result.final_position != current_final_pos:
            result.final_position = current_final_pos; final_pos_updates.append(result)
    if final_pos_updates: OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])


def update_overall_results_for_player(player: "Player") -> None:
    # Bez zmian
    for category in player.categories.all():
        update_discipline_positions(category)
        update_overall_results_for_category(category)
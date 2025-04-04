# W pliku services.py

from typing import TYPE_CHECKING
from django.db.models import Case, F, FloatField, Value, When # Upewnij się, że te importy są
from django.db.models.functions import Greatest             # na górze pliku services.py
# ... (inne importy na górze pliku) ...
from .constants import KB_SQUAT, ONE_KB_PRESS, PISTOL_SQUAT, SEE_SAW_PRESS, SNATCH, TGU, TWO_KB_PRESS
from .results.kb_squat import KBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult
from .results.snatch import SnatchResult
from .results.tgu import TGUResult
from .results.two_kettlebell_press import TwoKettlebellPressResult
# OverallResult nie jest tu potrzebny bezpośrednio

if TYPE_CHECKING:
    from .category import Category
    from .player import Player


def update_discipline_positions(category: "Category") -> None:
    """
    Calculates and updates the position for each player within a category
    for every active discipline in that category.
    TGU, One KB Press, KB Squat, Two KB Press are ranked based on score / body_weight.
    """
    from .player import Player

    players_in_category = Player.objects.filter(categories=category)
    if not players_in_category.exists():
        print(f"INFO: Brak graczy w kategorii {category.id}, pomijam update_discipline_positions.")
        return

    disciplines = category.get_disciplines()
    if not disciplines:
        print(f"INFO: Brak aktywnych dyscyplin w kategorii {category.id}, pomijam update_discipline_positions.")
        return

    discipline_models_map = {
        SNATCH: SnatchResult,
        TGU: TGUResult,
        SEE_SAW_PRESS: SeeSawPressResult,
        KB_SQUAT: KBSquatResult,
        PISTOL_SQUAT: PistolSquatResult,
        ONE_KB_PRESS: OneKettlebellPressResult,
        TWO_KB_PRESS: TwoKettlebellPressResult,
    }

    # Define scoring fields/annotations for ordering
    ordering_logic = {
        SNATCH: "-result",
        TGU: "-tgu_bw_ratio",          # ZMIENIONO
        PISTOL_SQUAT: "-max_pistol_result", # TODO: Zmień jeśli trzeba
        ONE_KB_PRESS: "-okbp_bw_ratio", # ZMIENIONO
        SEE_SAW_PRESS: "-max_ssp_score",    # Pozostaje bez zmian (chyba że chcesz %BW)
        KB_SQUAT: "-kbs_bw_ratio",     # ZMIENIONO
        TWO_KB_PRESS: "-tkbp_bw_ratio",  # ZMIENIONO
    }

    print(f"INFO: Rozpoczynam aktualizację pozycji dla kategorii {category.id} ({category.name})")
    for discipline in disciplines:
        if discipline not in discipline_models_map:
            print(f"OSTRZEŻENIE: Pominięto nieznaną dyscyplinę '{discipline}' w update_discipline_positions dla kategorii {category.id}")
            continue

        model = discipline_models_map[discipline]
        order_by_field = ordering_logic.get(discipline)

        if not order_by_field:
             print(f"OSTRZEŻENIE: Brak logiki sortowania dla dyscypliny '{discipline}' w update_discipline_positions dla kategorii {category.id}")
             continue

        print(f"--- INFO: Przetwarzam dyscyplinę: {discipline} dla kategorii {category.id} ---")

        results_qs = model.objects.select_related('player').filter(player__in=players_in_category)

        # === Dodaj adnotacje ===
        if discipline == TGU:
            results_qs = results_qs.annotate(
                max_tgu_result=Greatest("result_1", "result_2", "result_3")
            ).annotate(
                tgu_bw_ratio=Case(
                    When(player__weight__isnull=False, player__weight__gt=0, then=(F('max_tgu_result') / F('player__weight'))),
                    default=Value(0.0), output_field=FloatField()
                )
            )
        elif discipline == PISTOL_SQUAT:
             results_qs = results_qs.annotate(max_pistol_result=Greatest("result_1", "result_2", "result_3"))
             # TODO: Dodaj adnotację %BW, jeśli potrzebne
        elif discipline == ONE_KB_PRESS:
             results_qs = results_qs.annotate(
                 max_okbp_result=Greatest("result_1", "result_2", "result_3")
             ).annotate(
                 okbp_bw_ratio=Case(
                     When(player__weight__isnull=False, player__weight__gt=0, then=(F('max_okbp_result') / F('player__weight'))),
                     default=Value(0.0), output_field=FloatField()
                 )
             )
        elif discipline == SEE_SAW_PRESS:
            # Adnotacja dla max_ssp_score (suma L+R)
            results_qs = results_qs.annotate(
                ssp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F('result_left_1') + F('result_right_1')), default=Value(0.0), output_field=FloatField()),
                ssp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F('result_left_2') + F('result_right_2')), default=Value(0.0), output_field=FloatField()),
                ssp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F('result_left_3') + F('result_right_3')), default=Value(0.0), output_field=FloatField()),
            ).annotate(max_ssp_score=Greatest('ssp_score_1', 'ssp_score_2', 'ssp_score_3'))
            # TODO: Jeśli SSP też ma być wg %BW, dodaj tu adnotację 'ssp_bw_ratio' używając 'max_ssp_score'
        # V--- DODANO LOGIKĘ DLA KB SQUAT ---V
        elif discipline == KB_SQUAT:
             # 1. Oblicz max_kbs_score (suma L+R)
             results_qs = results_qs.annotate(
                kbs_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F('result_left_1') + F('result_right_1')), default=Value(0.0), output_field=FloatField()),
                kbs_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F('result_left_2') + F('result_right_2')), default=Value(0.0), output_field=FloatField()),
                kbs_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F('result_left_3') + F('result_right_3')), default=Value(0.0), output_field=FloatField()),
            ).annotate(
                max_kbs_score=Greatest('kbs_score_1', 'kbs_score_2', 'kbs_score_3')
            # 2. Oblicz kbs_bw_ratio
            ).annotate(
                 kbs_bw_ratio=Case(
                     When(player__weight__isnull=False, player__weight__gt=0,
                          then=(F('max_kbs_score') / F('player__weight'))),
                     default=Value(0.0), output_field=FloatField()
                 )
             )
        # ^--- KONIEC LOGIKI DLA KB SQUAT ---^
        # V--- DODANO LOGIKĘ DLA TWO KB PRESS ---V
        elif discipline == TWO_KB_PRESS:
             # 1. Oblicz max_tkbp_score (suma L+R)
             results_qs = results_qs.annotate(
                 tkbp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F('result_left_1') + F('result_right_1')), default=Value(0.0), output_field=FloatField()),
                 tkbp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F('result_left_2') + F('result_right_2')), default=Value(0.0), output_field=FloatField()),
                 tkbp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F('result_left_3') + F('result_right_3')), default=Value(0.0), output_field=FloatField()),
             ).annotate(
                 max_tkbp_score=Greatest('tkbp_score_1', 'tkbp_score_2', 'tkbp_score_3')
             # 2. Oblicz tkbp_bw_ratio
             ).annotate(
                  tkbp_bw_ratio=Case(
                     When(player__weight__isnull=False, player__weight__gt=0,
                          then=(F('max_tkbp_score') / F('player__weight'))),
                     default=Value(0.0), output_field=FloatField()
                 )
             )
        # ^--- KONIEC LOGIKI DLA TWO KB PRESS ---^

        # Sortuj wyniki
        ordered_results = results_qs.order_by(
            order_by_field, "player__surname", "player__name"
        )

        # Zaktualizuj pozycje
        updates = []
        current_pos = 0
        last_score = None
        rank_counter = 0
        for result in ordered_results:
            rank_counter += 1
            score = None
            try:
                if discipline == SNATCH: score = result.result
                elif discipline == TGU: score = result.tgu_bw_ratio # Używamy ratio
                elif discipline == PISTOL_SQUAT: score = result.max_pistol_result # TODO: Zmień na %BW jeśli trzeba
                elif discipline == ONE_KB_PRESS: score = result.okbp_bw_ratio # Używamy ratio
                elif discipline == SEE_SAW_PRESS: score = result.max_ssp_score # TODO: Zmień na %BW jeśli trzeba
                # V--- ZMIANA TUTAJ ---V
                elif discipline == KB_SQUAT: score = result.kbs_bw_ratio # Używamy ratio
                elif discipline == TWO_KB_PRESS: score = result.tkbp_bw_ratio # Używamy ratio
                # ^--- ZMIANA TUTAJ ---^
            except AttributeError as e:
                print(f"OSTRZEŻENIE: Brak atrybutu wyniku dla {discipline} u gracza {getattr(result, 'player_id', 'N/A')} ({e}). Ustawiam score na None.")
                score = None

            score_for_comparison = score if score is not None else -99999.0
            last_score_for_comparison = last_score if last_score is not None else -99999.0

            if score_for_comparison != last_score_for_comparison:
                 current_pos = rank_counter
                 last_score = score

            if result.position != current_pos:
                result.position = current_pos
                updates.append(result)

        if updates:
            try:
                model.objects.bulk_update(updates, ["position"])
                print(f"INFO: Zaktualizowano {len(updates)} pozycji dla dyscypliny {discipline} w kategorii {category.id}")
            except Exception as e_bulk:
                print(f"!!!!!!!!!! BŁĄD: Błąd podczas bulk_update pozycji dla {discipline} w kat. {category.id}: {e_bulk} !!!!!!!!!!!")

    print(f"INFO: Zakończono aktualizację pozycji dla kategorii {category.id} ({category.name})")

# ... (reszta pliku services.py - update_overall_results_for_category i update_overall_results_for_player)

def update_overall_results_for_category(category: "Category") -> None:
    """
    Calculates and updates overall scores and final positions for all players
    within a specific category based on their discipline positions.
    """
    from .player import Player # Import Player do użycia w funkcji
    from .results.overall import OverallResult # Import OverallResult do użycia w funkcji
    # ^--- DODAJ TEN IMPORT ---^
    from .player import Player # Ten import już tu prawdopodobnie jest lub powinien być

    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        "snatch_result",
        "tgu_result",
        "pistol_squat_result",
        "see_saw_press_result",
        "kb_squat_result",
        "one_kettlebell_press_result",
        "two_kettlebell_press_result",
    )
    disciplines = category.get_disciplines()

    overall_updates = []

    # 1. Calculate points based on position in each active discipline
    for player in players_in_category:
        # ... (reszta logiki obliczania punktów bez zmian) ...
        overall_result, created = OverallResult.objects.get_or_create(player=player)

        # Reset points
        overall_result.snatch_points = 0.0
        overall_result.tgu_points = 0.0
        overall_result.see_saw_press_points = 0.0
        overall_result.kb_squat_points = 0.0
        overall_result.pistol_squat_points = 0.0
        overall_result.one_kb_press_points = 0.0
        overall_result.two_kb_press_points = 0.0
        overall_result.tiebreak_points = -0.5 if player.tiebreak else 0.0

        # Assign points based on position
        # ... (przypisywanie punktów) ...
        if SNATCH in disciplines and hasattr(player, "snatch_result") and player.snatch_result.position is not None:
            overall_result.snatch_points = float(player.snatch_result.position)
        if TGU in disciplines and hasattr(player, "tgu_result") and player.tgu_result.position is not None:
            overall_result.tgu_points = float(player.tgu_result.position)
        if (
            SEE_SAW_PRESS in disciplines
            and hasattr(player, "see_saw_press_result")
            and player.see_saw_press_result.position is not None
        ):
            overall_result.see_saw_press_points = float(player.see_saw_press_result.position)
        if (
            KB_SQUAT in disciplines
            and hasattr(player, "kb_squat_result")
            and player.kb_squat_result.position is not None
        ):
            overall_result.kb_squat_points = float(player.kb_squat_result.position)
        if (
            PISTOL_SQUAT in disciplines
            and hasattr(player, "pistol_squat_result")
            and player.pistol_squat_result.position is not None
        ):
            overall_result.pistol_squat_points = float(player.pistol_squat_result.position)
        if (
            ONE_KB_PRESS in disciplines
            and hasattr(player, "one_kettlebell_press_result")
            and player.one_kettlebell_press_result.position is not None
        ):
            overall_result.one_kb_press_points = float(player.one_kettlebell_press_result.position)
        if (
            TWO_KB_PRESS in disciplines
            and hasattr(player, "two_kettlebell_press_result")
            and player.two_kettlebell_press_result.position is not None
        ):
            overall_result.two_kb_press_points = float(player.two_kettlebell_press_result.position)

        overall_result.calculate_total_points()
        overall_updates.append(overall_result)

    # Bulk update points
    if overall_updates:
        OverallResult.objects.bulk_update(
            overall_updates,
            [
                "snatch_points",
                "tgu_points",
                "see_saw_press_points",
                "kb_squat_points",
                "pistol_squat_points",
                "one_kb_press_points",
                "two_kb_press_points",
                "tiebreak_points",
                "total_points",
            ],
        )

    # 2. Determine final positions
    # ... (logika obliczania final_position bez zmian) ...
    final_results = OverallResult.objects.filter(player__in=players_in_category).order_by(
        "total_points", "player__surname", "player__name"
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
        OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])


def update_overall_results_for_player(player: "Player") -> None:
    """Updates overall results for all categories the player belongs to."""
    # Należy zaktualizować pozycje we wszystkich kategoriach gracza
    # i przeliczyć wyniki ogólne dla tych kategorii.
    for category in player.categories.all():
        # Najpierw zaktualizuj pozycje w dyscyplinach dla całej kategorii
        update_discipline_positions(category)
        # Następnie zaktualizuj wyniki ogólne dla całej kategorii
        update_overall_results_for_category(category)

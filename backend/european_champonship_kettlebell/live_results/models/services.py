# services.py
# W pliku services.py

from typing import TYPE_CHECKING

from django.db.models import Case, F, FloatField, Value, When
from django.db.models.functions import Greatest

# Importuj stałe i modele wyników
from .constants import KB_SQUAT, ONE_KB_PRESS, PISTOL_SQUAT, SEE_SAW_PRESS, SNATCH, TGU, TWO_KB_PRESS
from .results.kb_squat import KBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult
from .results.snatch import SnatchResult
from .results.tgu import TGUResult  # Upewnij się, że TGUResult jest importowany
from .results.two_kettlebell_press import TwoKettlebellPressResult

# OverallResult jest importowany wewnątrz funkcji update_overall_results_for_category

if TYPE_CHECKING:
    from .category import Category
    from .player import Player


def update_discipline_positions(category: "Category") -> None:
    """
    Calculates and updates the position for each player within a category
    for every active discipline in that category.
    TGU, One KB Press, KB Squat, Two KB Press are ranked based on score / body_weight.
    """
    from .player import Player  # Import lokalny

    players_in_category = Player.objects.filter(categories=category)
    if not players_in_category.exists():
        # print(f"INFO: Brak graczy w kategorii {category.id}, pomijam update_discipline_positions.")
        return

    disciplines = category.get_disciplines()
    if not disciplines:
        # print(f"INFO: Brak aktywnych dyscyplin w kategorii {category.id}, pomijam update_discipline_positions.")
        return

    # Mapa dyscyplin na modele wyników
    discipline_models_map = {
        SNATCH: SnatchResult,
        TGU: TGUResult,  # Poprawnie mapuje na TGUResult
        SEE_SAW_PRESS: SeeSawPressResult,
        KB_SQUAT: KBSquatResult,
        PISTOL_SQUAT: PistolSquatResult,
        ONE_KB_PRESS: OneKettlebellPressResult,
        TWO_KB_PRESS: TwoKettlebellPressResult,
    }

    # Logika sortowania dla każdej dyscypliny (wyższy wynik jest lepszy)
    ordering_logic = {
        SNATCH: "-result",  # Wyższy wynik Snatch (waga * powtórzenia) jest lepszy
        TGU: "-tgu_bw_ratio",  # Wyższy stosunek %BW jest lepszy
        PISTOL_SQUAT: "-max_pistol_result",  # Wyższy ciężar jest lepszy (można zmienić na %BW)
        ONE_KB_PRESS: "-okbp_bw_ratio",  # Wyższy stosunek %BW jest lepszy
        SEE_SAW_PRESS: "-max_ssp_score",  # Wyższa suma L+R jest lepsza (można zmienić na %BW)
        KB_SQUAT: "-kbs_bw_ratio",  # Wyższy stosunek %BW jest lepszy
        TWO_KB_PRESS: "-tkbp_bw_ratio",  # Wyższy stosunek %BW jest lepszy
    }

    # print(f"INFO: Rozpoczynam aktualizację pozycji dla kategorii {category.id} ({category.name})")
    for discipline in disciplines:
        if discipline not in discipline_models_map:
            # print(f"OSTRZEŻENIE: Pominięto nieznaną dyscyplinę '{discipline}'...")
            continue

        model = discipline_models_map[discipline]
        order_by_field = ordering_logic.get(discipline)

        if not order_by_field:
            # print(f"OSTRZEŻENIE: Brak logiki sortowania dla dyscypliny '{discipline}'...")
            continue

        # print(f"--- INFO: Przetwarzam dyscyplinę: {discipline} dla kategorii {category.id} ---")

        results_qs = model.objects.select_related("player").filter(player__in=players_in_category)

        # === Dodaj adnotacje do obliczeń wyników/stosunków %BW ===
        # Adnotacje pozwalają na obliczenia w bazie danych, co jest wydajniejsze

        if discipline == TGU:
            # Oblicz max wynik TGU i stosunek do wagi ciała (%BW)
            results_qs = results_qs.annotate(
                max_tgu_result=Greatest(
                    F("result_1"), F("result_2"), F("result_3"), Value(0.0)
                )  # Uwzględnij 0.0 jako minimum
            ).annotate(
                tgu_bw_ratio=Case(
                    When(
                        player__weight__isnull=False,
                        player__weight__gt=0,
                        max_tgu_result__gt=0,  # Dodaj warunek, że wynik musi być > 0
                        then=(F("max_tgu_result") / F("player__weight")),
                    ),
                    default=Value(0.0),  # Domyślnie 0, jeśli waga lub wynik nie pozwalają
                    output_field=FloatField(),
                )
            )
        elif discipline == PISTOL_SQUAT:
            # Oblicz max wynik Pistol
            results_qs = results_qs.annotate(
                max_pistol_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0))
            )
            # TODO: Jeśli Pistol też ma być wg %BW, dodaj tu adnotację 'pistol_bw_ratio'
        elif discipline == ONE_KB_PRESS:
            # Oblicz max wynik OKBP i stosunek do wagi ciała (%BW)
            results_qs = results_qs.annotate(
                max_okbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0))
            ).annotate(
                okbp_bw_ratio=Case(
                    When(
                        player__weight__isnull=False,
                        player__weight__gt=0,
                        max_okbp_result__gt=0,
                        then=(F("max_okbp_result") / F("player__weight")),
                    ),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        elif discipline == SEE_SAW_PRESS:
            # Oblicz sumy L+R dla każdej próby i znajdź maksymalną sumę
            results_qs = results_qs.annotate(
                ssp_score_1=Case(
                    When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                ssp_score_2=Case(
                    When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                ssp_score_3=Case(
                    When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            ).annotate(max_ssp_score=Greatest("ssp_score_1", "ssp_score_2", "ssp_score_3"))
            # TODO: Jeśli SSP też ma być wg %BW, dodaj tu adnotację 'ssp_bw_ratio'
        elif discipline == KB_SQUAT:
            # Oblicz sumy L+R, max sumę i stosunek %BW
            results_qs = (
                results_qs.annotate(
                    kbs_score_1=Case(
                        When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    kbs_score_2=Case(
                        When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    kbs_score_3=Case(
                        When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                )
                .annotate(max_kbs_score=Greatest("kbs_score_1", "kbs_score_2", "kbs_score_3"))
                .annotate(
                    kbs_bw_ratio=Case(
                        When(
                            player__weight__isnull=False,
                            player__weight__gt=0,
                            max_kbs_score__gt=0,
                            then=(F("max_kbs_score") / F("player__weight")),
                        ),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            )
        elif discipline == TWO_KB_PRESS:
            # Oblicz sumy L+R, max sumę i stosunek %BW
            results_qs = (
                results_qs.annotate(
                    tkbp_score_1=Case(
                        When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    tkbp_score_2=Case(
                        When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                    tkbp_score_3=Case(
                        When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    ),
                )
                .annotate(max_tkbp_score=Greatest("tkbp_score_1", "tkbp_score_2", "tkbp_score_3"))
                .annotate(
                    tkbp_bw_ratio=Case(
                        When(
                            player__weight__isnull=False,
                            player__weight__gt=0,
                            max_tkbp_score__gt=0,
                            then=(F("max_tkbp_score") / F("player__weight")),
                        ),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            )

        # Sortuj wyniki zgodnie z logiką dla dyscypliny
        # Dodajemy sortowanie po nazwisku i imieniu jako drugi i trzeci klucz dla stabilności
        ordered_results = results_qs.order_by(order_by_field, "player__surname", "player__name")

        # === Zaktualizuj pozycje z obsługą remisów ===
        updates = []
        current_pos = 0
        last_score = None  # Używamy None do oznaczenia braku poprzedniego wyniku
        rank_counter = 0  # Licznik wszystkich przetworzonych wyników (wliczając te z 0)
        pos_counter = 0  # Licznik pozycji (numer miejsca)

        for result in ordered_results:
            rank_counter += 1
            score = None  # Domyślnie brak wyniku
            try:
                # Pobierz odpowiedni wynik (lub ratio) do rankingu
                if discipline == SNATCH:
                    score = result.result
                elif discipline == TGU:
                    score = result.tgu_bw_ratio
                elif discipline == PISTOL_SQUAT:
                    score = result.max_pistol_result
                elif discipline == ONE_KB_PRESS:
                    score = result.okbp_bw_ratio
                elif discipline == SEE_SAW_PRESS:
                    score = result.max_ssp_score
                elif discipline == KB_SQUAT:
                    score = result.kbs_bw_ratio
                elif discipline == TWO_KB_PRESS:
                    score = result.tkbp_bw_ratio
            except AttributeError:
                # print(f"OSTRZEŻENIE: Brak atrybutu wyniku dla {discipline}...")
                score = 0.0  # Traktuj brak wyniku jako 0 dla porównań

            # Normalizuj None do 0.0 dla porównań, ale zachowaj None dla logiki
            score_for_comparison = score if score is not None else 0.0
            last_score_for_comparison = (
                last_score if last_score is not None else -1.0
            )  # Użyj wartości niemożliwej do osiągnięcia

            # Sprawdź czy wynik się zmienił (obsługa float)
            # Użyj małej tolerancji epsilon dla porównania liczb zmiennoprzecinkowych
            epsilon = 1e-6
            if abs(score_for_comparison - last_score_for_comparison) > epsilon:
                # Jeśli wynik się zmienił, aktualna pozycja to bieżący rank_counter
                current_pos = rank_counter
                last_score = score  # Zapisz nowy ostatni wynik

            # Przypisz obliczoną pozycję tylko jeśli się różni
            if result.position != current_pos:
                result.position = current_pos
                updates.append(result)

        # Zaktualizuj pozycje masowo
        if updates:
            try:
                model.objects.bulk_update(updates, ["position"])
                # print(f"INFO: Zaktualizowano {len(updates)} pozycji dla {discipline}...")
            except Exception as e_bulk:
                print(
                    f"!!!!!!!!!! BŁĄD: Błąd podczas bulk_update pozycji dla {discipline} w kat. {category.id}: {e_bulk} !!!!!!!!!!!"
                )
                # W produkcji: logowanie błędu

    # print(f"INFO: Zakończono aktualizację pozycji dla kategorii {category.id} ({category.name})")


def update_overall_results_for_category(category: "Category") -> None:
    """
    Calculates and updates overall scores and final positions for all players
    within a specific category based on their discipline positions.
    """
    from .player import Player  # Import lokalny
    from .results.overall import OverallResult  # Import lokalny

    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        # Prefetch related results models to avoid N+1 queries
        "snatch_result",
        "tgu_result",  # Wynik TGU
        "pistol_squat_result",
        "see_saw_press_result",
        "kb_squat_result",
        "one_kettlebell_press_result",  # Wynik OKBP
        "two_kettlebell_press_result",
    )
    disciplines = category.get_disciplines()

    overall_updates = []

    # 1. Calculate points based on position in each active discipline
    for player in players_in_category:
        overall_result, created = OverallResult.objects.get_or_create(player=player)

        # Reset points before recalculation
        overall_result.snatch_points = None
        overall_result.tgu_points = None
        overall_result.see_saw_press_points = None
        overall_result.kb_squat_points = None
        overall_result.pistol_squat_points = None
        overall_result.one_kb_press_points = None
        overall_result.two_kb_press_points = None
        overall_result.tiebreak_points = -0.5 if player.tiebreak else 0.0

        # Assign points based on position (lower position = fewer points, better rank)
        # Handle cases where a result object might not exist or position is None
        def get_points(discipline_name, result_attr_name):
            if discipline_name in disciplines:
                result_obj = getattr(player, result_attr_name, None)
                if result_obj and result_obj.position is not None:
                    return float(result_obj.position)
            return None  # Return None if discipline inactive or result missing

        overall_result.snatch_points = get_points(SNATCH, "snatch_result")
        overall_result.tgu_points = get_points(TGU, "tgu_result")
        overall_result.see_saw_press_points = get_points(SEE_SAW_PRESS, "see_saw_press_result")
        overall_result.kb_squat_points = get_points(KB_SQUAT, "kb_squat_result")
        overall_result.pistol_squat_points = get_points(PISTOL_SQUAT, "pistol_squat_result")
        overall_result.one_kb_press_points = get_points(ONE_KB_PRESS, "one_kettlebell_press_result")
        overall_result.two_kb_press_points = get_points(TWO_KB_PRESS, "two_kettlebell_press_result")

        # Calculate total points (summing points, treating None as 0 for sum)
        overall_result.calculate_total_points()  # Ta metoda powinna obsługiwać None
        overall_updates.append(overall_result)

    # Bulk update points if any updates were prepared
    if overall_updates:
        update_fields = [
            "snatch_points",
            "tgu_points",
            "see_saw_press_points",
            "kb_squat_points",
            "pistol_squat_points",
            "one_kb_press_points",
            "two_kb_press_points",
            "tiebreak_points",
            "total_points",
        ]
        OverallResult.objects.bulk_update(overall_updates, update_fields)

    # 2. Determine final positions based on total_points (lower is better)
    # Fetch updated results for ranking
    final_results = OverallResult.objects.filter(player__in=players_in_category).order_by(
        "total_points",  # Lower total points is better
        "player__surname",  # Tiebreaker 1: Surname
        "player__name",  # Tiebreaker 2: Name
    )

    final_pos_updates = []
    current_final_pos = 0
    last_total_points = None  # Use None to mark the start
    rank_counter = 0  # Counter for assigning rank number

    for result in final_results:
        rank_counter += 1
        # Compare current total points with the last one
        # Handle None for the very first player
        if last_total_points is None or result.total_points != last_total_points:
            current_final_pos = rank_counter  # New rank starts
            last_total_points = result.total_points

        # Update final position if it changed
        if result.final_position != current_final_pos:
            result.final_position = current_final_pos
            final_pos_updates.append(result)

    # Bulk update final positions if any changes were made
    if final_pos_updates:
        OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])


def update_overall_results_for_player(player: "Player") -> None:
    """Updates results for all categories the player belongs to."""
    # Gdy zawodnik jest zapisywany, musimy przeliczyć wyniki
    # we wszystkich kategoriach, do których należy.
    for category in player.categories.all():
        # 1. Aktualizuj pozycje w poszczególnych dyscyplinach dla całej kategorii
        update_discipline_positions(category)
        # 2. Następnie zaktualizuj punkty ogólne i pozycje końcowe dla całej kategorii
        update_overall_results_for_category(category)

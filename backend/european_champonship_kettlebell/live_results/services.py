# Pełna zawartość pliku services.py

import traceback
from django.db import transaction
from django.db.models import Case, F, FloatField, Value, When, IntegerField # Dodano IntegerField
from django.db.models.functions import Greatest

# Upewnij się, że ścieżki importów są poprawne dla Twojego projektu
from .models import Category, Player
from .models.constants import KB_SQUAT, ONE_KB_PRESS, SNATCH, TGU, TWO_KB_PRESS # Usunięto nieużywane
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    OverallResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)

# Używaj stałych z constants
DISCIPLINE_MODELS_MAP = {
    SNATCH: SnatchResult,
    TGU: TGUResult,
    KB_SQUAT: KBSquatResult,
    ONE_KB_PRESS: OneKettlebellPressResult,
    TWO_KB_PRESS: TwoKettlebellPressResult,
}

DEFAULT_RESULT_VALUES = {
    SNATCH: {"kettlebell_weight": 0, "repetitions": 0},
    TGU: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    ONE_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    KB_SQUAT: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    TWO_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
}

DISCIPLINE_RELATED_NAMES = {
    SNATCH: "snatch_result",
    TGU: "tgu_result",
    KB_SQUAT: "kb_squat_one_result", # Sprawdź related_name w modelu Player!
    ONE_KB_PRESS: "one_kettlebell_press_result",
    TWO_KB_PRESS: "two_kettlebell_press_one_result", # Sprawdź related_name w modelu Player!
}

# Mapowanie pól punktowych w OverallResult
OVERALL_POINTS_FIELDS = {
    SNATCH: "snatch_points",
    TGU: "tgu_points",
    KB_SQUAT: "kb_squat_points",
    ONE_KB_PRESS: "one_kb_press_points",
    TWO_KB_PRESS: "two_kb_press_points",
}

# Logika sortowania dla rankingu w dyscyplinach
# Używane w update_discipline_positions i get_player_rank_in_discipline
DISCIPLINE_ORDERING_LOGIC = {
    SNATCH: "-calculated_snatch_score", # Wynik = Waga * Powtórzenia
    TGU: "-tgu_bw_ratio",               # Wynik = % masy ciała
    ONE_KB_PRESS: "-okbp_bw_ratio",       # Wynik = % masy ciała
    KB_SQUAT: "-kbs_bw_ratio",           # Wynik = % masy ciała
    TWO_KB_PRESS: "-tkbp_bw_ratio",       # Wynik = % masy ciała
}

def update_discipline_positions(category: Category) -> None:
    """
    Calculates and updates positions for players within a category
    for each relevant discipline. Includes detailed debugging prints.
    NOTE: This function updates the 'position' field on individual result models,
          which might not be strictly necessary with the new get_rank logic,
          but the ranking calculation itself is reused.
    """
    print(f"\n=== DEBUG: Rozpoczynam update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===")

    players_in_category = Player.objects.filter(categories=category).only("id", "weight", "surname", "name")
    if not players_in_category.exists():
        print(f"DEBUG: Brak graczy w kategorii {category.id} ('{category.name}'). Pomijam obliczanie pozycji dyscyplin.")
        print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (Brak graczy) ===")
        return

    player_ids = list(players_in_category.values_list("id", flat=True))
    print(f"DEBUG: Znaleziono graczy w kategorii (IDs): {player_ids}")

    disciplines = category.get_disciplines()
    if not disciplines:
        print(f"DEBUG: Kategoria {category.id} ('{category.name}') nie ma zdefiniowanych dyscyplin. Pomijam obliczanie pozycji.")
        print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (Brak dyscyplin) ===")
        return

    print(f"DEBUG: Dyscypliny do przetworzenia w kategorii: {disciplines}")
    for discipline in disciplines:
        print(f"\n  --- DEBUG: Przetwarzanie dyscypliny: {discipline} ---")

        if discipline not in DISCIPLINE_MODELS_MAP:
            print(f"  DEBUG WARNING: Pomijam nieznaną dyscyplinę '{discipline}' w kategorii {category.id}")
            continue

        model = DISCIPLINE_MODELS_MAP[discipline]
        order_by_field = DISCIPLINE_ORDERING_LOGIC.get(discipline) # Użycie mapy stałych
        if not order_by_field:
            print(f"  DEBUG WARNING: Brak logiki sortowania dla dyscypliny '{discipline}'. Pomijam.")
            continue

        print(f"  DEBUG: Model={model.__name__}, Sortowanie po={order_by_field}")
        results_qs = model.objects.select_related("player").filter(player_id__in=player_ids)

        # Adnotacje do obliczenia wyniku sortującego
        annotated_qs = results_qs
        annotation_field_name = None

        try:
            # --- Logika Adnotacji (niezmieniona - zakłada istnienie pól w modelach!) ---
            if discipline == SNATCH:
                annotation_field_name = "calculated_snatch_score"
                annotated_qs = results_qs.annotate(
                    calculated_snatch_score=Case(
                        When(kettlebell_weight__gt=0, repetitions__gt=0, then=F("kettlebell_weight") * F("repetitions")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            elif discipline == TGU:
                annotation_field_name = "tgu_bw_ratio"
                annotated_qs = results_qs.annotate(
                    max_tgu_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
                ).annotate(
                    tgu_bw_ratio=Case(
                        When(player__weight__gt=0, max_tgu_result__gt=0, then=F("max_tgu_result") / F("player__weight")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            elif discipline == ONE_KB_PRESS:
                annotation_field_name = "okbp_bw_ratio"
                annotated_qs = results_qs.annotate(
                    max_okbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
                ).annotate(
                    okbp_bw_ratio=Case(
                        When(player__weight__gt=0, max_okbp_result__gt=0, then=F("max_okbp_result") / F("player__weight")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            elif discipline == KB_SQUAT:
                annotation_field_name = "kbs_bw_ratio"
                annotated_qs = results_qs.annotate(
                    max_kbs_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
                ).annotate(
                    kbs_bw_ratio=Case(
                        When(player__weight__gt=0, max_kbs_result__gt=0, then=F("max_kbs_result") / F("player__weight")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            elif discipline == TWO_KB_PRESS:
                annotation_field_name = "tkbp_bw_ratio"
                annotated_qs = results_qs.annotate(
                    max_tkbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
                ).annotate(
                    tkbp_bw_ratio=Case(
                        When(player__weight__gt=0, max_tkbp_result__gt=0, then=F("max_tkbp_result") / F("player__weight")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )
                )
            # --- Koniec Logiki Adnotacji ---

            if not annotation_field_name:
                 print(f"  DEBUG ERROR: Nie udało się ustalić pola adnotacji dla {discipline}. Pomijam ranking.")
                 continue

            # Sortowanie
            ordered_results = annotated_qs.order_by(order_by_field, "player__surname", "player__name")
            print(f"  DEBUG: Wyniki posortowane. Liczba wyników: {ordered_results.count()}")

            updates = []
            current_pos = 0
            last_score = None
            rank_counter = 0
            tie_start_rank = 1

            # Logika remisu (bez epsilon, jak prosiłeś)
            print(f"    --- DEBUG: Rozpoczynam pętlę rankingu dla {discipline} ---")
            for result in ordered_results:
                rank_counter += 1
                player_str = f"{result.player.surname} {result.player.name}" if result.player else f"Gracz ID:{result.player_id}"
                score = 0.0
                try:
                    score = float(getattr(result, annotation_field_name, 0.0) or 0.0)
                except (AttributeError, TypeError, ValueError) as e_score:
                    score = 0.0
                    print(f"      DEBUG WARNING: Błąd pobierania score ({annotation_field_name}) dla {player_str}: {e_score}")

                # Logika remisu z bezpośrednim porównaniem
                is_tie = False
                if last_score is not None:
                    if score == last_score: # Bezpośrednie porównanie
                        is_tie = True

                if not is_tie:
                    current_pos = rank_counter
                    last_score = score
                    tie_start_rank = rank_counter
                else:
                    current_pos = tie_start_rank

                db_position = result.position
                needs_update = False
                if db_position != current_pos or db_position is None:
                    needs_update = True
                    result.position = current_pos # Aktualizuj pole position obiektu
                    updates.append(result)

                # Usunięto część logów dla zwięzłości
                # print(f"      DEBUG: Iter {rank_counter}, Player: {player_str}, Score: {score:.4f}, LastScore: {last_score:.4f if last_score is not None else 'N/A'}, IsTie: {is_tie}, TieStart: {tie_start_rank}, CalcPos: {current_pos}, DBPos: {db_position}, NeedsUpd: {needs_update}")

            print(f"    --- DEBUG: Zakończono pętlę rankingu. Liczba potencjalnych aktualizacji: {len(updates)} ---")

            if updates:
                try:
                    with transaction.atomic(): # Zapewnia atomowość bulk_update
                        updated_count = model.objects.bulk_update(updates, ["position"])
                    print(f"    DEBUG SUCCESS: Zaktualizowano pozycje dla {updated_count} rekordów w {discipline}.")
                except Exception as e_bulk:
                    print(f"    DEBUG ERROR: BŁĄD bulk_update pozycji dla {discipline} w kategorii {category.id}: {e_bulk}")
                    traceback.print_exc()
            else:
                print(f"    DEBUG INFO: Brak zmian pozycji do zapisania dla {discipline}.")

        except Exception as e_outer:
            print(f"  DEBUG ERROR: Niespodziewany błąd podczas przetwarzania dyscypliny {discipline} w kategorii {category.id}: {e_outer}")
            traceback.print_exc()
        print(f"  --- DEBUG: Zakończono przetwarzanie dyscypliny: {discipline} ---")
    print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===")


# --- NOWA Funkcja pomocnicza do obliczania rankingu ---
def get_player_rank_in_discipline(player: Player, discipline: str, category: Category) -> int | None:
    """
    Oblicza i zwraca ranking (miejsce) danego gracza w konkretnej dyscyplinie
    i kategorii, poprawnie obsługując remisy.

    UWAGA: Ta funkcja powtarza logikę rankingu i może być mniej wydajna
           przy dużej liczbie wywołań.
    """
    print(f"    DEBUG (get_rank): Obliczanie rankingu dla gracza {player.id} w {discipline} (kat: {category.id})")
    model = DISCIPLINE_MODELS_MAP.get(discipline)
    if not model:
        print(f"    DEBUG (get_rank): Nie znaleziono modelu dla {discipline}")
        return None

    players_in_category_ids = list(Player.objects.filter(categories=category).values_list("id", flat=True))
    if player.id not in players_in_category_ids:
        print(f"    DEBUG (get_rank): Gracz {player.id} nie należy do kategorii {category.id}")
        return None

    results_qs = model.objects.filter(player_id__in=players_in_category_ids).select_related('player')
    order_by_field = DISCIPLINE_ORDERING_LOGIC.get(discipline)
    if not order_by_field:
        print(f"    DEBUG (get_rank): Brak logiki sortowania dla {discipline}")
        return None

    annotated_qs = results_qs
    annotation_field_name = None
    # --- POCZĄTEK: Logika Adnotacji (taka sama jak w update_discipline_positions) ---
    try:
        if discipline == SNATCH:
            annotation_field_name = "calculated_snatch_score"
            annotated_qs = results_qs.annotate(
                calculated_snatch_score=Case(
                    When(kettlebell_weight__gt=0, repetitions__gt=0, then=F("kettlebell_weight") * F("repetitions")),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        elif discipline == TGU:
            annotation_field_name = "tgu_bw_ratio"
            annotated_qs = results_qs.annotate(
                max_tgu_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                tgu_bw_ratio=Case(
                    When(player__weight__gt=0, max_tgu_result__gt=0, then=F("max_tgu_result") / F("player__weight")),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        elif discipline == ONE_KB_PRESS:
            annotation_field_name = "okbp_bw_ratio"
            annotated_qs = results_qs.annotate(
                max_okbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                okbp_bw_ratio=Case(
                    When(player__weight__gt=0, max_okbp_result__gt=0, then=F("max_okbp_result") / F("player__weight")),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        elif discipline == KB_SQUAT:
            annotation_field_name = "kbs_bw_ratio"
            annotated_qs = results_qs.annotate(
                max_kbs_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                kbs_bw_ratio=Case(
                    When(player__weight__gt=0, max_kbs_result__gt=0, then=F("max_kbs_result") / F("player__weight")),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        elif discipline == TWO_KB_PRESS:
            annotation_field_name = "tkbp_bw_ratio"
            annotated_qs = results_qs.annotate(
                max_tkbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                tkbp_bw_ratio=Case(
                    When(player__weight__gt=0, max_tkbp_result__gt=0, then=F("max_tkbp_result") / F("player__weight")),
                    default=Value(0.0),
                    output_field=FloatField(),
                )
            )
        else:
             print(f"    DEBUG (get_rank) WARNING: Brak specyficznej adnotacji dla {discipline}.")
             return None
    # --- KONIEC: Logika Adnotacji ---

        if not annotation_field_name:
             print(f"    DEBUG (get_rank) ERROR: Nie udało się ustalić pola adnotacji dla {discipline}.")
             return None

        ordered_results = annotated_qs.order_by(order_by_field, "player__surname", "player__name")

        current_rank = 0
        last_score = None
        rank_counter = 0
        tie_start_rank = 1
        player_rank = None

        for index, result in enumerate(ordered_results):
            rank_counter += 1
            score = 0.0
            try:
                score = float(getattr(result, annotation_field_name, 0.0) or 0.0)
            except (AttributeError, TypeError, ValueError):
                score = 0.0

            # Logika remisu (bez epsilon)
            is_tie = False
            if last_score is not None:
                if score == last_score: # Bezpośrednie porównanie
                    is_tie = True

            calculated_rank_for_this_iteration = 0
            if not is_tie:
                calculated_rank_for_this_iteration = rank_counter
                last_score = score
                tie_start_rank = rank_counter
            else:
                calculated_rank_for_this_iteration = tie_start_rank

            if result.player_id == player.id:
                player_rank = calculated_rank_for_this_iteration
                print(f"    DEBUG (get_rank): Znaleziono ranking {player_rank} dla gracza {player.id} w {discipline} (kat: {category.id})")
                break

        if player_rank is None:
             print(f"    DEBUG (get_rank) WARNING: Nie znaleziono gracza {player.id} w posortowanych wynikach {discipline} (kat: {category.id})?")

        return player_rank

    except Exception as e:
        print(f"    DEBUG (get_rank) ERROR: Błąd podczas obliczania rankingu dla gracza {player.id} w {discipline} (kat: {category.id}): {e}")
        traceback.print_exc()
        return None


# --- ZMODYFIKOWANA funkcja update_overall_results_for_category ---
def update_overall_results_for_category(category: Category) -> None:
    """
    Oblicza i aktualizuje punkty ogólne i pozycje końcowe dla graczy
    w ramach danej kategorii. Używa get_player_rank_in_discipline do pobrania
    poprawnego rankingu dla każdej dyscypliny w kontekście kategorii.
    """
    players_in_category = Player.objects.filter(categories=category) # Pobierz graczy tylko raz
    player_ids_in_category = list(players_in_category.values_list('id', flat=True)) # Pobierz ID

    if not player_ids_in_category:
        print(f"Brak graczy w kategorii {category.id}. Pomijam obliczanie wyników ogólnych.")
        return

    print(f"Aktualizacja wyników ogólnych dla kategorii: {category.name} ({category.id}) dla graczy: {player_ids_in_category}")
    disciplines_in_category = category.get_disciplines()
    overall_results_map = { # Słownik dla szybkiego dostępu
        or_obj.player_id: or_obj
        for or_obj in OverallResult.objects.filter(player_id__in=player_ids_in_category)
    }
    overall_updates = []
    final_pos_updates = []

    # --- Pętla po graczach w kategorii ---
    for player_id in player_ids_in_category:
        # Użyj mapy lub get_or_create
        overall_result = overall_results_map.get(player_id)
        created_overall = False
        if not overall_result:
            try:
                # Musimy mieć pełny obiekt Player do stworzenia OverallResult
                player_obj = Player.objects.get(pk=player_id)
                overall_result, created_overall = OverallResult.objects.get_or_create(player=player_obj)
                if created_overall:
                    print(f"  Stworzono brakujący rekord OverallResult dla gracza {player_id}")
                    overall_results_map[player_id] = overall_result # Dodaj do mapy
                else: # Jeśli jakimś cudem istniał, a nie było w mapie
                     overall_results_map[player_id] = overall_result
            except Player.DoesNotExist:
                 print(f"  BŁĄD KRYTYCZNY: Nie można znaleźć gracza {player_id} do stworzenia OverallResult!")
                 continue # Pomiń tego gracza

        changed = False # Flaga czy OverallResult gracza wymaga zapisu

        # Pobierz obiekt gracza (potrzebny do tiebreak i get_player_rank)
        try:
             current_player = Player.objects.get(pk=player_id)
        except Player.DoesNotExist:
             print(f"  BŁĄD KRYTYCZNY: Gracz {player_id} zniknął w trakcie przetwarzania!")
             continue

        # 1. Wyczyść stare punkty dyscyplin
        for field_name in OVERALL_POINTS_FIELDS.values():
            if getattr(overall_result, field_name, None) is not None:
                setattr(overall_result, field_name, None)
                changed = True

        # 2. Ustaw punkty Tiebreak
        new_tiebreak_points = -0.5 if current_player.tiebreak else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True

        # 3. Oblicz i przypisz punkty dla każdej dyscypliny w kategorii
        print(f"  Obliczanie punktów dla gracza: {player_id} ({current_player})")
        for disc_const in disciplines_in_category:
            points_field = OVERALL_POINTS_FIELDS.get(disc_const)
            if not points_field: continue

            # Wywołaj nową funkcję pomocniczą
            calculated_rank = get_player_rank_in_discipline(current_player, disc_const, category)
            new_points = float(calculated_rank) if calculated_rank is not None else None

            print(f"    Dyscyplina: {disc_const}, Obliczony Rank: {calculated_rank}, Przypisane Punkty: {new_points}")

            if getattr(overall_result, points_field, None) != new_points:
                setattr(overall_result, points_field, new_points)
                changed = True

        # 4. Oblicz sumę punktów
        old_total_points = overall_result.total_points
        overall_result.calculate_total_points()
        print(f"    Obliczono total_points: {overall_result.total_points} (poprzednio: {old_total_points})")
        if old_total_points != overall_result.total_points:
            changed = True

        # 5. Dodaj do listy do aktualizacji
        if changed or created_overall:
            overall_updates.append(overall_result)
    # --- Koniec pętli po graczach ---

    # 6. Zapisz zmiany w punktach
    if overall_updates:
        update_fields = list(OVERALL_POINTS_FIELDS.values()) + ["tiebreak_points", "total_points"]
        try:
            updated_points_count = OverallResult.objects.bulk_update(overall_updates, update_fields)
            print(f"  Zaktualizowano punkty OverallResult dla {updated_points_count} graczy.")
        except Exception as e_bulk_overall:
            print(f"  BŁĄD bulk_update punktów OverallResult w kategorii {category.id}: {e_bulk_overall}")
            traceback.print_exc()
    else:
         print("  Brak zmian punktów OverallResult do zapisania.")

    # 7. Oblicz i zaktualizuj MIEJSCA KOŃCOWE
    # Pobierz ponownie OverallResult posortowane wg zasad rankingu generalnego
    final_results = OverallResult.objects.filter(player_id__in=player_ids_in_category).annotate(
        total_points_is_null=Case(When(total_points__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField())
    ).order_by(
        'total_points_is_null', # Nulls last
        "total_points",         # Lower points better
        "player__surname",      # Then by name
        "player__name"
    )

    current_final_pos = 0
    last_total_points = None
    final_rank_counter = 0
    tie_start_rank_final = 1 # Do poprawnej obsługi remisów w final_position (1, 2, 3, 3, 5)

    print(f"\n  Obliczanie Miejsc Końcowych (final_position) dla {final_results.count()} wyników...")
    for result in final_results:
        final_rank_counter += 1
        current_total_points = result.total_points

        # Logika remisu dla final_position (porównujemy total_points)
        is_tie_final = False
        # Sprawdzamy tylko jeśli oba nie są None
        if current_total_points is not None and last_total_points is not None:
            # Użyjemy bezpośredniego porównania
            if current_total_points == last_total_points:
                 is_tie_final = True
        elif current_total_points is None and last_total_points is None:
             # Traktujmy dwa None jako remis, jeśli trzeba
             is_tie_final = True

        calculated_final_pos_for_iteration = 0
        if not is_tie_final: # Nie ma remisu lub pierwszy rekord
            calculated_final_pos_for_iteration = final_rank_counter
            last_total_points = current_total_points
            tie_start_rank_final = final_rank_counter # Zapamiętaj rangę początku (potencjalnego) remisu
        else: # Jest remis
            calculated_final_pos_for_iteration = tie_start_rank_final # Użyj rangi początku remisu

        # Porównaj i dodaj do aktualizacji, jeśli konieczne
        if result.final_position != calculated_final_pos_for_iteration or result.final_position is None:
            result.final_position = calculated_final_pos_for_iteration
            final_pos_updates.append(result)
            print(f"    Aktualizacja final_position dla {result.player_id}: {calculated_final_pos_for_iteration}")

    # 8. Zapisz zmiany w miejscach końcowych
    if final_pos_updates:
        try:
            updated_pos_count = OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  Zaktualizowano final_position OverallResult dla {updated_pos_count} graczy.")
        except Exception as e_bulk_final:
            print(f"  BŁĄD bulk_update final_position OverallResult w kategorii {category.id}: {e_bulk_final}")
            traceback.print_exc()
    else:
        print("  Brak zmian final_position OverallResult do zapisania.")


# --- Funkcja update_overall_results_for_player (z dekoratorem transakcji) ---
@transaction.atomic # Cała operacja jako jedna transakcja
def update_overall_results_for_player(player: Player) -> None:
    """
    Aktualizuje pozycje w dyscyplinach i wyniki ogólne dla WSZYSTKICH kategorii,
    do których należy gracz. Obejmuje całość transakcją atomową.
    """
    if not hasattr(player, "categories"):
        print(f"Obiekt gracza {player.id} nie ma atrybutu 'categories'. Pomijam aktualizację.")
        return

    # Pobierz kategorie w ramach transakcji
    try:
        # Użyj select_for_update jeśli spodziewasz się konkurencyjnych zapisów,
        # ale na razie zwykłe pobranie powinno wystarczyć w ramach @transaction.atomic
        categories = list(player.categories.all())
    except Exception as e_fetch:
        print(f"BŁĄD podczas pobierania kategorii dla gracza {player.id}: {e_fetch}")
        return # Przerwij jeśli nie można pobrać kategorii

    if not categories:
        print(f"Gracz {player.id} nie ma przypisanych kategorii. Pomijam aktualizację overall.")
        return

    print(f"=== Rozpoczynam pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    try:
        # Pętla po kategoriach gracza
        print(f"Aktualizuję wyniki dla gracza {player.id} w kategoriach: {[c.name for c in categories]}")
        for category in categories:
            print(f"\n--- Aktualizacja dla Kategorii: {category.name} ({category.id}) ---")
            # Mimo że update_discipline_positions zapisuje pozycję na głównym obiekcie,
            # wykonanie jej tutaj nie zaszkodzi, a może być potrzebne dla innych celów.
            update_discipline_positions(category)

            # Ta funkcja teraz używa get_player_rank_in_discipline, więc jest kluczowa
            update_overall_results_for_category(category)

        print(f"=== Zakończono pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    except Exception as e:
        print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id}: {e}")
        traceback.print_exc()
        # Transakcja zostanie automatycznie wycofana dzięki @transaction.atomic


# --- Funkcja create_default_results_for_player_categories (bez zmian) ---
# Upewnij się, że ta funkcja jest obecna w Twoim pliku, skopiowana z oryginalnego services.py
# Ta funkcja powinna używać globalnych map DISCIPLINE_MODELS_MAP i DEFAULT_RESULT_VALUES
# zdefiniowanych na górze tego pliku.
# @transaction.atomic # Ta funkcja może być atomowa sama w sobie
def create_default_results_for_player_categories(player: Player, category_pks: set[int]):
    """
    Creates default (zeroed) result entries for a player in disciplines
    associated with newly assigned categories. Uses get_or_create to avoid duplicates.
    Returns True if any new record was created, False otherwise.
    """
    if not category_pks:
        return False

    created_new = False
    # Dodajemy .select_related('competition') jeśli Competition jest w modelu Category i potrzebne
    categories_to_process = Category.objects.filter(pk__in=category_pks)
    print(
        f"Tworzenie domyślnych wyników dla gracza {player.id} w kategoriach: {[c.name for c in categories_to_process]}"
    )

    for category in categories_to_process:
        disciplines_in_category = category.get_disciplines()
        if not disciplines_in_category:
            print(f"  Kategoria {category.name} nie ma dyscyplin.")
            continue

        print(f"  Przetwarzanie kategorii: {category.name}")
        for discipline_key in disciplines_in_category:
            model_class = DISCIPLINE_MODELS_MAP.get(discipline_key)
            if model_class:
                defaults = DEFAULT_RESULT_VALUES.get(discipline_key, {}).copy()

                # Używamy transaction.atomic dla pewności przy get_or_create
                try:
                    with transaction.atomic():
                         obj, created = model_class.objects.get_or_create(player=player, defaults=defaults)
                    if created:
                        created_new = True
                        print(f"    + Stworzono domyślny rekord {model_class.__name__} dla gracza {player.id}")
                except Exception as e_get_create:
                     print(f"   ! BŁĄD get_or_create dla {model_class.__name__}, gracz {player.id}: {e_get_create}")

            else:
                print(
                    f"    ! OSTRZEŻENIE: Nie znaleziono modelu dla dyscypliny '{discipline_key}' w kategorii {category.id}"
                )

    return created_new

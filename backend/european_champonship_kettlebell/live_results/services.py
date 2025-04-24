# Plik: services.py

import traceback
from django.db import transaction
from django.db.models import Case, F, FloatField, Value, When, IntegerField
from django.db.models.functions import Greatest

# Importuj NOWY model CategoryOverallResult i upewnij się, że reszta importów jest poprawna
from .models import Category, Player
from .models.constants import KB_SQUAT, ONE_KB_PRESS, SNATCH, TGU, TWO_KB_PRESS
from .models.results.overall import CategoryOverallResult
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)

# Mapy stałych (bez zmian, ale upewnij się, że są aktualne)
DISCIPLINE_MODELS_MAP = {
    SNATCH: SnatchResult, TGU: TGUResult, KB_SQUAT: KBSquatResult,
    ONE_KB_PRESS: OneKettlebellPressResult, TWO_KB_PRESS: TwoKettlebellPressResult,
}
DISCIPLINE_RELATED_NAMES = {
    SNATCH: "snatch_result", TGU: "tgu_result", KB_SQUAT: "kb_squat_one_result", # Sprawdź related_name!
    ONE_KB_PRESS: "one_kettlebell_press_result", TWO_KB_PRESS: "two_kettlebell_press_one_result", # Sprawdź related_name!
}
OVERALL_POINTS_FIELDS = {
    SNATCH: "snatch_points", TGU: "tgu_points", KB_SQUAT: "kb_squat_points",
    ONE_KB_PRESS: "one_kb_press_points", TWO_KB_PRESS: "two_kb_press_points",
}
DISCIPLINE_ORDERING_LOGIC = {
    SNATCH: "-calculated_snatch_score", TGU: "-tgu_bw_ratio", ONE_KB_PRESS: "-okbp_bw_ratio",
    KB_SQUAT: "-kbs_bw_ratio", TWO_KB_PRESS: "-tkbp_bw_ratio",
}
DEFAULT_RESULT_VALUES = { # Potwierdź wartości domyślne
    SNATCH: {"kettlebell_weight": 0, "repetitions": 0},
    TGU: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    ONE_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    KB_SQUAT: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
    TWO_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0, "max_result_val": 0.0, "bw_percentage_val": 0.0},
}

# --- Funkcja update_discipline_positions (BEZ ZMIAN FUNKCJONALNYCH) ---
# Nadal oblicza ranking w dyscyplinie i zapisuje w polu 'position'
# indywidualnych wyników (np. SnatchResult.position).
def update_discipline_positions(category: Category) -> None:
    """Oblicza i aktualizuje pozycje graczy w dyscyplinach DLA DANEJ KATEGORII."""
    print(f"\n=== DEBUG: Rozpoczynam update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===")

    players_in_category = Player.objects.filter(categories=category).only("id", "weight", "surname", "name")
    if not players_in_category.exists():
        print(f"DEBUG: Brak graczy w kategorii {category.id}. Pomijam.")
        return

    player_ids = list(players_in_category.values_list("id", flat=True))
    disciplines = category.get_disciplines()
    if not disciplines:
        print(f"DEBUG: Kategoria {category.id} nie ma dyscyplin. Pomijam.")
        return

    print(f"DEBUG: Dyscypliny do przetworzenia: {disciplines}")
    for discipline in disciplines:
        print(f"\n  --- DEBUG: Przetwarzanie dyscypliny: {discipline} ---")

        model = DISCIPLINE_MODELS_MAP.get(discipline)
        order_by_field = DISCIPLINE_ORDERING_LOGIC.get(discipline)
        if not model or not order_by_field:
            print(f"  DEBUG WARNING: Brak modelu lub logiki sortowania dla '{discipline}'. Pomijam.")
            continue

        results_qs = model.objects.select_related("player").filter(player_id__in=player_ids)
        annotated_qs = results_qs
        annotation_field_name = None

        try:
            # --- Logika Adnotacji (zakłada istnienie pól result_1/2/3 w modelach!) ---
            if discipline == SNATCH:
                annotation_field_name = "calculated_snatch_score"
                annotated_qs = results_qs.annotate(calculated_snatch_score=Case(When(kettlebell_weight__gt=0, repetitions__gt=0, then=F("kettlebell_weight") * F("repetitions")), default=Value(0.0), output_field=FloatField()))
            elif discipline in [TGU, ONE_KB_PRESS, KB_SQUAT, TWO_KB_PRESS]: # Wspólna logika dla %MC
                base_name = discipline.lower()
                max_res_field = f"max_{base_name}_result"
                ratio_field = f"{base_name}_bw_ratio"
                annotation_field_name = ratio_field
                # WAŻNE: Upewnij się, że modele TGU, OKBP, KBS, TKBP mają pola result_1, result_2, result_3
                annotated_qs = results_qs.annotate(
                    **{max_res_field: Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())}
                ).annotate(
                    **{ratio_field: Case(
                        When(**{f'player__weight__gt': 0, f'{max_res_field}__gt': 0}, then=F(max_res_field) / F("player__weight")),
                        default=Value(0.0),
                        output_field=FloatField(),
                    )}
                )
            # --- Koniec Logiki Adnotacji ---

            if not annotation_field_name:
                 print(f"  DEBUG ERROR: Nie ustalono pola adnotacji dla {discipline}. Pomijam.")
                 continue

            ordered_results = annotated_qs.order_by(order_by_field, "player__surname", "player__name")
            print(f"  DEBUG: Wyniki posortowane ({ordered_results.count()}).")

            updates = []
            current_pos = 0
            last_score = None
            rank_counter = 0
            tie_start_rank = 1

            # Logika remisu (bez epsilon)
            print(f"    --- DEBUG: Pętla rankingu dla {discipline} ---")
            for result in ordered_results:
                rank_counter += 1
                score = float(getattr(result, annotation_field_name, 0.0) or 0.0)

                is_tie = False
                if last_score is not None and score == last_score:
                    is_tie = True

                if not is_tie:
                    current_pos = rank_counter
                    last_score = score
                    tie_start_rank = rank_counter
                else:
                    current_pos = tie_start_rank

                if result.position != current_pos or result.position is None:
                    result.position = current_pos
                    updates.append(result)

            print(f"    --- DEBUG: Koniec pętli rankingu. Aktualizacje: {len(updates)} ---")

            if updates:
                try:
                    with transaction.atomic():
                        updated_count = model.objects.bulk_update(updates, ["position"])
                    print(f"    DEBUG SUCCESS: Zaktualizowano 'position' dla {updated_count} rekordów {model.__name__}.")
                except Exception as e_bulk:
                    print(f"    DEBUG ERROR: BŁĄD bulk_update 'position' dla {model.__name__}: {e_bulk}")
                    traceback.print_exc()
            else:
                print(f"    DEBUG INFO: Brak zmian 'position' do zapisania dla {model.__name__}.")

        except Exception as e_outer:
            print(f"  DEBUG ERROR: Niespodziewany błąd przetwarzania dyscypliny {discipline}: {e_outer}")
            traceback.print_exc()
        print(f"  --- DEBUG: Koniec przetwarzania dyscypliny: {discipline} ---")
    print(f"=== DEBUG: Koniec update_discipline_positions dla kategorii: {category.name} ===")


# --- ZMODYFIKOWANA funkcja update_overall_results_for_category (Uproszczona) ---
def update_overall_results_for_category(category: Category) -> None:
    """
    Oblicza i aktualizuje punkty ogólne i pozycje końcowe dla graczy
    W RAMACH DANEJ KATEGORII, operując na modelu CategoryOverallResult.
    Odczytuje obliczone wcześniej pozycje z indywidualnych wyników.
    """
    player_ids_in_category = list(Player.objects.filter(categories=category).values_list('id', flat=True))

    if not player_ids_in_category:
        print(f"Brak graczy w kat. {category.id}. Pomijam update_overall_results_for_category.")
        CategoryOverallResult.objects.filter(category=category).delete() # Usuń stare wyniki, jeśli nie ma graczy
        return

    print(f"Aktualizacja CategoryOverallResult dla kat: {category.name} ({category.id}), gracze: {player_ids_in_category}")
    disciplines_in_category = category.get_disciplines()

    # Pobierz indywidualne wyniki (tylko player_id i position) dla optymalizacji
    discipline_positions = {}
    for disc_const in disciplines_in_category:
        model_class = DISCIPLINE_MODELS_MAP.get(disc_const)
        if model_class:
            results = model_class.objects.filter(player_id__in=player_ids_in_category).values('player_id', 'position')
            discipline_positions[disc_const] = {r['player_id']: r['position'] for r in results}

    # Pobierz istniejące CategoryOverallResult i obiekty Player
    players_map = {p.id: p for p in Player.objects.filter(id__in=player_ids_in_category)}
    overall_results_map = {
        or_obj.player_id: or_obj
        for or_obj in CategoryOverallResult.objects.filter(category=category, player_id__in=player_ids_in_category)
    }
    overall_updates = []
    final_pos_updates = []

    # --- Pętla po ID graczy w kategorii ---
    for player_id in player_ids_in_category:
        player = players_map.get(player_id)
        if not player: continue # Na wszelki wypadek

        # Pobierz lub stwórz CategoryOverallResult dla gracza i kategorii
        overall_result = overall_results_map.get(player_id)
        created_overall = False
        if not overall_result:
            overall_result, created_overall = CategoryOverallResult.objects.get_or_create(player=player, category=category)
            if created_overall: print(f"  Stworzono CategoryOverallResult dla gracza {player_id} w kat {category.id}")
        else: print(f"  Aktualizacja CategoryOverallResult dla gracza {player_id} w kat {category.id}")

        changed = False

        # 1. Wyczyść/Ustaw punkty Tiebreak
        new_tiebreak_points = -0.5 if player.tiebreak else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True

        # 2. Przypisz punkty na podstawie odczytanej pozycji
        for disc_const in disciplines_in_category:
            points_field = OVERALL_POINTS_FIELDS.get(disc_const)
            if not points_field: continue

            position = discipline_positions.get(disc_const, {}).get(player_id)
            new_points = float(position) if position is not None else None

            print(f"    Dyscyplina: {disc_const}, Odczytana Pozycja: {position}, Przypisane Punkty: {new_points}")
            if getattr(overall_result, points_field, None) != new_points:
                setattr(overall_result, points_field, new_points)
                changed = True
        # Wyzeruj punkty dla dyscyplin spoza kategorii (jeśli były wcześniej)
        for disc_const, points_field in OVERALL_POINTS_FIELDS.items():
             if disc_const not in disciplines_in_category:
                  if getattr(overall_result, points_field, None) is not None:
                       setattr(overall_result, points_field, None)
                       changed = True


        # 3. Oblicz sumę punktów
        old_total_points = overall_result.total_points
        overall_result.calculate_total_points()
        print(f"    Obliczono total_points: {overall_result.total_points} (poprzednio: {old_total_points})")
        if old_total_points != overall_result.total_points:
            changed = True

        # 4. Dodaj do listy do aktualizacji
        if changed or created_overall:
            overall_updates.append(overall_result)
            # Zaktualizuj mapę, aby mieć najnowszy obiekt do obliczenia final_position
            overall_results_map[player_id] = overall_result


    # 5. Zapisz zmiany w punktach (bulk_create/update)
    if overall_updates:
        to_create = [res for res in overall_updates if res.pk is None]
        to_update = [res for res in overall_updates if res.pk is not None]
        update_fields = list(OVERALL_POINTS_FIELDS.values()) + ["tiebreak_points", "total_points"]
        try:
            if to_create: CategoryOverallResult.objects.bulk_create(to_create)
            if to_update: CategoryOverallResult.objects.bulk_update(to_update, update_fields)
            print(f"  Zapisano zmiany punktów dla {len(to_create)} (nowych) i {len(to_update)} (istniejących) CategoryOverallResult.")
             # Zaktualizuj obiekty w mapie po bulk_create, aby miały PK
            if to_create:
                new_results_map = {or_obj.player_id: or_obj for or_obj in CategoryOverallResult.objects.filter(category=category, player_id__in=[p.id for p in to_create])}
                overall_results_map.update(new_results_map)
        except Exception as e_bulk:
            print(f"  BŁĄD bulk operacji CategoryOverallResult (punkty) w kat {category.id}: {e_bulk}")
            traceback.print_exc()
    else:
         print("  Brak zmian punktów CategoryOverallResult do zapisania.")

    # 6. Oblicz i zaktualizuj MIEJSCA KOŃCOWE (final_position) DLA TEJ KATEGORII
    # Pobierz wszystkie (potencjalnie zaktualizowane) wyniki dla tej kategorii
    final_results_qs = CategoryOverallResult.objects.filter(
        category=category,
        player_id__in=player_ids_in_category
    ).annotate(
        total_points_is_null=Case(When(total_points__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField())
    ).select_related('player') # Potrzebne do sortowania po nazwisku
    # Sortuj wg punktów (nulls last), potem nazwiska
    final_results_list = list(final_results_qs.order_by(
        'total_points_is_null', "total_points", "player__surname", "player__name"
    ))

    current_final_pos = 0
    last_total_points = None
    final_rank_counter = 0
    tie_start_rank_final = 1

    print(f"\n  Obliczanie Miejsc Końcowych (final_position) dla {len(final_results_list)} wyników w kat. {category.id}...")
    for result in final_results_list: # Iteruj po liście obiektów z pamięci
        final_rank_counter += 1
        current_total_points = result.total_points

        is_tie_final = False
        if current_total_points is not None and last_total_points is not None:
            if current_total_points == last_total_points: is_tie_final = True
        elif current_total_points is None and last_total_points is None: is_tie_final = True

        calculated_final_pos_for_iteration = 0
        if not is_tie_final:
            calculated_final_pos_for_iteration = final_rank_counter
            last_total_points = current_total_points
            tie_start_rank_final = final_rank_counter
        else:
            calculated_final_pos_for_iteration = tie_start_rank_final

        if result.final_position != calculated_final_pos_for_iteration or result.final_position is None:
            result.final_position = calculated_final_pos_for_iteration # Zmień obiekt w pamięci
            final_pos_updates.append(result) # Dodaj do listy do aktualizacji
            print(f"    Aktualizacja final_position dla gracza {result.player_id} w kat {category.id}: {calculated_final_pos_for_iteration}")

    if final_pos_updates:
        try:
            updated_pos_count = CategoryOverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  Zaktualizowano final_position CategoryOverallResult dla {updated_pos_count} graczy w kat {category.id}.")
        except Exception as e_bulk_final:
            print(f"  BŁĄD bulk_update final_position CategoryOverallResult w kat {category.id}: {e_bulk_final}")
            traceback.print_exc()
    else:
        print(f"  Brak zmian final_position CategoryOverallResult do zapisania w kat {category.id}.")
    print(f"--- Koniec update_overall_results_for_category dla kat: {category.name} ---")


# --- Funkcja update_overall_results_for_player (z dekoratorem transakcji) ---
@transaction.atomic
def update_overall_results_for_player(player: Player) -> None:
    """
    Aktualizuje wyniki dla WSZYSTKICH kategorii gracza.
    """
    if not hasattr(player, "categories"):
        print(f"Gracz {player.id} nie ma 'categories'. Pomijam.")
        return

    try:
        # Użyj prefetch_related dla optymalizacji, jeśli Category ma dużo relacji
        categories = list(player.categories.prefetch_related('disciplines_relation')) # Załóżmy, że tak się nazywa M2M do Discipline
    except Exception as e_fetch:
        print(f"BŁĄD pobierania kategorii dla gracza {player.id}: {e_fetch}")
        return

    if not categories:
        print(f"Gracz {player.id} nie ma kategorii. Pomijam.")
        # Usuń stare wyniki gracza we wszystkich kategoriach
        # CategoryOverallResult.objects.filter(player=player).delete()
        return

    print(f"=== Rozpoczynam pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    try:
        print(f"Aktualizuję wyniki dla gracza {player.id} w kategoriach: {[c.name for c in categories]}")
        for category in categories:
            print(f"\n--- Aktualizacja dla Kategorii: {category.name} ({category.id}) ---")
            # 1. Oblicz pozycje w dyscyplinach dla tej kategorii (zapisuje w SnatchResult.position itp.)
            update_discipline_positions(category)
            # 2. Oblicz wyniki ogólne dla tej kategorii (odczytuje pozycje z kroku 1)
            update_overall_results_for_category(category)
        print(f"=== Zakończono pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    except Exception as e:
        print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id}: {e}")
        traceback.print_exc()


# --- Funkcja create_default_results_for_player_categories (bez zmian) ---
# Tworzy domyślne SnatchResult, TGUResult itp.
def create_default_results_for_player_categories(player: Player, category_pks: set[int]):
    """Tworzy domyślne rekordy wyników dyscyplin."""
    if not category_pks: return False
    created_new = False
    categories_to_process = Category.objects.filter(pk__in=category_pks)
    print(f"Tworzenie domyślnych wyników dyscyplin dla gracza {player.id} w kat: {[c.name for c in categories_to_process]}")
    for category in categories_to_process:
        disciplines_in_category = category.get_disciplines()
        if not disciplines_in_category: continue
        print(f"  Przetwarzanie kategorii: {category.name}")
        for discipline_key in disciplines_in_category:
            model_class = DISCIPLINE_MODELS_MAP.get(discipline_key)
            if model_class:
                defaults = DEFAULT_RESULT_VALUES.get(discipline_key, {}).copy()
                try:
                    with transaction.atomic():
                         obj, created = model_class.objects.get_or_create(player=player, defaults=defaults)
                    if created:
                        created_new = True
                        print(f"    + Stworzono domyślny rekord {model_class.__name__} dla gracza {player.id}")
                except Exception as e_get_create:
                     print(f"   ! BŁĄD get_or_create dla {model_class.__name__}, gracz {player.id}: {e_get_create}")
            else:
                print(f"    ! OSTRZEŻENIE: Nie znaleziono modelu dla dyscypliny '{discipline_key}'")
    return created_new
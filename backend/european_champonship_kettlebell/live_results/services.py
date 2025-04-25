# Plik: services.py

import traceback
from django.db import transaction
from django.db.models import Case, F, FloatField, Value, When, IntegerField
from django.db.models.functions import Greatest
from .models.tiebreak import PlayerCategoryTiebreak

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
    SNATCH: "-calculated_snatch_score",
    TGU: "-tgu_bw_ratio", # Było OK
    # ZMIENIONO PONIŻSZE vvv
    ONE_KB_PRESS: "-one_kettlebell_press_bw_ratio",
    KB_SQUAT: "-kb_squat_bw_ratio",
    TWO_KB_PRESS: "-two_kettlebell_press_bw_ratio",
    # KONIEC ZMIAN ^^^
}
DEFAULT_RESULT_VALUES = { # Potwierdź wartości domyślne
    SNATCH: {"kettlebell_weight": 0.0, "repetitions": 0}, # Użyj 0.0 dla FloatField
    # Usunięto 'max_result_val' i 'bw_percentage_val' z poniższych
    TGU: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
    ONE_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
    KB_SQUAT: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
    TWO_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
}

# --- Funkcja update_discipline_positions (BEZ ZMIAN FUNKCJONALNYCH) ---
# Nadal oblicza ranking w dyscyplinie i zapisuje w polu 'position'
# indywidualnych wyników (np. SnatchResult.position).
def update_discipline_positions(category: Category) -> None:
    """Oblicza i aktualizuje pozycje graczy w dyscyplinach DLA DANEJ KATEGORII."""

    print(f"\n=== DEBUG: Rozpoczynam update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===")
    DEBUG_DISCIPLINES = {KB_SQUAT, ONE_KB_PRESS, TWO_KB_PRESS}

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


def update_overall_results_for_category(category: Category) -> None:
    """
    Oblicza i aktualizuje punkty ogólne i pozycje końcowe dla graczy
    W RAMACH DANEJ KATEGORII, operując na modelu CategoryOverallResult.
    Odczytuje obliczone wcześniej pozycje z indywidualnych wyników.
    """
    player_ids_in_category = list(Player.objects.filter(categories=category).values_list('id', flat=True))
    DEBUG_DISCIPLINES = {KB_SQUAT, ONE_KB_PRESS, TWO_KB_PRESS}

    if not player_ids_in_category:
        print(f"Brak graczy w kat. {category.id}. Pomijam update_overall_results_for_category.")
        # Rozważ usunięcie starych wyników, jeśli logika biznesowa tego wymaga
        # CategoryOverallResult.objects.filter(category=category).delete()
        return

    print(f"Aktualizacja CategoryOverallResult dla kat: {category.name} ({category.id}), gracze: {player_ids_in_category}")
    disciplines_in_category = category.get_disciplines()

    # Pobierz indywidualne wyniki (tylko player_id i position) dla optymalizacji
    discipline_positions = {}
    # Dodano print debugujący
    print(f"\n[DEBUG OVERALL - {category.id}] Pobieranie pozycji dla dyscyplin: {disciplines_in_category}")
    for disc_const in disciplines_in_category:
        model_class = DISCIPLINE_MODELS_MAP.get(disc_const)
        if model_class:
            # Upewnij się, że pole 'position' istnieje w modelu
            try:
                results = model_class.objects.filter(player_id__in=player_ids_in_category).values('player_id', 'position')
                discipline_positions[disc_const] = {r['player_id']: r['position'] for r in results}
                 # Dodano blok print debugujący
                if disc_const in DEBUG_DISCIPLINES:
                    print(f"  [DEBUG OVERALL - {category.id}] Pozycje dla {disc_const}: {discipline_positions[disc_const]}")
            except Exception as e_val:
                 print(f"  BŁĄD pobierania pozycji dla {model_class.__name__} w kat {category.id}: {e_val}")
                 discipline_positions[disc_const] = {} # Ustaw pusty słownik w razie błędu

    players_map = {p.id: p for p in Player.objects.filter(id__in=player_ids_in_category)}
    # Pobierz istniejące wyniki Overall dla tej kategorii i graczy
    overall_results_map = {
        or_obj.player_id: or_obj
        for or_obj in CategoryOverallResult.objects.filter(category=category, player_id__in=player_ids_in_category)
    }
    overall_updates = []
    final_pos_updates = []
    tiebreak_info = set(
        PlayerCategoryTiebreak.objects.filter(
            category=category,
            player_id__in=player_ids_in_category
        ).values_list('player_id', flat=True)
    )
    print(f"  [DEBUG OVERALL - {category.id}] Gracze z tiebreakiem w tej kat: {tiebreak_info}") # Log debugujący
    for player_id in player_ids_in_category:
        player = players_map.get(player_id)
        if not player: continue

        overall_result = overall_results_map.get(player_id)
        created_overall = False
        if not overall_result:
            # Użyj get_or_create dla bezpieczeństwa, jeśli jakimś cudem mapa jest niekompletna
            overall_result, created_overall = CategoryOverallResult.objects.get_or_create(
                player=player,
                category=category,
                # Można dodać defaults={}, ale get_or_create i tak użyje domyślnych modelu
            )
            if created_overall: print(f"  Stworzono CategoryOverallResult dla gracza {player_id} w kat {category.id}")
            overall_results_map[player_id] = overall_result # Dodaj do mapy, jeśli stworzono
        # else: print(f"  Aktualizacja CategoryOverallResult dla gracza {player_id} w kat {category.id}") # Mniej istotny log

        changed = False # Flaga śledząca, czy cokolwiek się zmieniło dla tego gracza

        # Aktualizuj punkty tiebreak
        apply_tiebreak_for_this_category = player_id in tiebreak_info
        new_tiebreak_points = -0.5 if apply_tiebreak_for_this_category else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True
            print(f"    [DEBUG OVERALL - {category.id}] Aktualizacja tiebreak_points dla gracza {player_id} na {new_tiebreak_points}") # Log debugujący

        # Dodano print debugujący
        print(f"  [DEBUG OVERALL - {category.id}] Przypisywanie punktów dla gracza: {player_id} ({player})")
        for disc_const in disciplines_in_category:
            points_field = OVERALL_POINTS_FIELDS.get(disc_const)
            if not points_field: continue # Pomiń, jeśli dyscyplina nie ma mapowania na pole punktowe

            # Odczytujemy 'position' z wcześniej pobranych danych
            # Używamy .get(player_id) z domyślnym None, aby uniknąć KeyError
            position = discipline_positions.get(disc_const, {}).get(player_id) # Bezpieczny dostęp
            # Konwertuj pozycję na float lub None
            new_points = float(position) if position is not None else None

            # Dodano blok print debugujący
            if disc_const in DEBUG_DISCIPLINES:
                 print(f"    [DEBUG OVERALL - {category.id}] Dyscyplina: {disc_const}, Gracz: {player_id}")
                 print(f"      -> Odczytana Pozycja: {position}")
                 print(f"      -> Pole punktowe: {points_field}")
                 print(f"      -> Przypisane Punkty (new_points): {new_points}")

            # Sprawdź, czy wartość się zmieniła przed ustawieniem
            if getattr(overall_result, points_field, None) != new_points:
                setattr(overall_result, points_field, new_points)
                changed = True
                # Dodano print informujący o zmianie
                if disc_const in DEBUG_DISCIPLINES:
                    print(f"      *** ZMIANA punktów {points_field} dla gracza {player_id} na {new_points} ***")

        # Wyzeruj punkty dla dyscyplin spoza kategorii
        # (Ważne, jeśli gracz zmienił kategorię lub dyscypliny w kategorii zostały usunięte)
        for disc_const_all, points_field_all in OVERALL_POINTS_FIELDS.items():
             if disc_const_all not in disciplines_in_category:
                  if getattr(overall_result, points_field_all, None) is not None:
                       setattr(overall_result, points_field_all, None)
                       changed = True
                       print(f"    [DEBUG OVERALL - {category.id}] Zerowanie punktów {points_field_all} dla gracza {player_id} (dyscyplina poza kat.)")


        # Oblicz sumę punktów po aktualizacji pól dyscyplin
        old_total_points = overall_result.total_points
        overall_result.calculate_total_points() # Wywołaj metodę z modelu
        print(f"    [DEBUG OVERALL - {category.id}] Obliczono total_points: {overall_result.total_points} (poprzednio: {old_total_points})")
        if old_total_points != overall_result.total_points:
            changed = True

        # Jeśli cokolwiek się zmieniło (lub obiekt został dopiero stworzony), dodaj go do listy do zapisu
        if changed or created_overall:
            # Nie dodawaj do overall_updates, jeśli obiekt dopiero co został stworzony przez get_or_create
            # Dodaj go tylko jeśli istniał i się zmienił
            if not created_overall and changed:
                 overall_updates.append(overall_result)


    # Zapisz zmiany punktów za pomocą bulk_update (tylko dla istniejących i zmienionych)
    if overall_updates:
        update_fields = list(OVERALL_POINTS_FIELDS.values()) + ["tiebreak_points", "total_points"]
        try:
            # Dodano print debugujący
            print(f"  [DEBUG OVERALL - {category.id}] Próba bulk_update dla pól: {update_fields}")
            updated_points_count = CategoryOverallResult.objects.bulk_update(overall_updates, update_fields)
             # Dodano print debugujący
            print(f"  [DEBUG OVERALL - {category.id}] Wynik bulk_update (punkty): {updated_points_count} rekordów.")
        except Exception as e_bulk:
            print(f"  BŁĄD bulk operacji CategoryOverallResult (punkty) w kat {category.id}: {e_bulk}")
            traceback.print_exc()
    else:
         print(f"  [DEBUG OVERALL - {category.id}] Brak zmian punktów CategoryOverallResult do zapisania (poza nowo stworzonymi).")


    # --- Oblicz i zaktualizuj MIEJSCA KOŃCOWE (final_position) ---
    # Pobierz WSZYSTKIE wyniki dla kategorii (w tym te nowo stworzone)
    final_results_qs = CategoryOverallResult.objects.filter(
        category=category, player_id__in=player_ids_in_category
    ).annotate(
        # Pomocnicza adnotacja do sortowania - nulls last dla total_points
        total_points_is_null=Case(When(total_points__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField())
    ).select_related('player') # select_related dla dostępu do player__surname etc.

    # Sortuj wg total_points (niskie lepsze, nulls last), potem nazwiska
    final_results_list = list(final_results_qs.order_by(
        'total_points_is_null', "total_points", "player__surname", "player__name"
    ))

    current_final_pos = 0
    last_total_points = None # Śledzi ostatni wynik do obsługi remisów
    final_rank_counter = 0 # Licznik pozycji w pętli
    tie_start_rank_final = 1 # Zapamiętuje pozycję, od której zaczął się remis

    print(f"\n  [DEBUG OVERALL - {category.id}] Obliczanie Miejsc Końcowych dla {len(final_results_list)} wyników...")
    for result in final_results_list:
        final_rank_counter += 1
        current_total_points = result.total_points # Może być None

        is_tie_final = False
        # Sprawdź remis (tylko jeśli oba wyniki nie są None LUB oba są None)
        if current_total_points is not None and last_total_points is not None:
            # Użyj porównania z tolerancją dla float? Na razie dokładne.
            if current_total_points == last_total_points: is_tie_final = True
        elif current_total_points is None and last_total_points is None: is_tie_final = True # Dwa None to też "remis" na końcu listy

        calculated_final_pos_for_iteration = 0
        if not is_tie_final:
            # Nowy wynik (lub pierwszy wynik) -> nowa pozycja
            calculated_final_pos_for_iteration = final_rank_counter
            last_total_points = current_total_points # Zaktualizuj ostatni wynik
            tie_start_rank_final = final_rank_counter # Zapamiętaj pozycję startową potencjalnego remisu
        else:
            # Remis -> użyj pozycji startowej remisu
            calculated_final_pos_for_iteration = tie_start_rank_final

        # Sprawdź, czy pozycja się zmieniła
        if result.final_position != calculated_final_pos_for_iteration or result.final_position is None:
            result.final_position = calculated_final_pos_for_iteration
            final_pos_updates.append(result) # Dodaj do listy do aktualizacji
            # print(f"    Aktualizacja final_position dla gracza {result.player_id} w kat {category.id}: {calculated_final_pos_for_iteration}") # Mniej istotny log

    # Zapisz zmiany miejsc końcowych za pomocą bulk_update
    if final_pos_updates:
        try:
            updated_pos_count = CategoryOverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  [DEBUG OVERALL - {category.id}] Zaktualizowano final_position CategoryOverallResult dla {updated_pos_count} graczy.")
        except Exception as e_bulk_final:
            print(f"  BŁĄD bulk_update final_position CategoryOverallResult w kat {category.id}: {e_bulk_final}")
            traceback.print_exc()
    else:
        print(f"  [DEBUG OVERALL - {category.id}] Brak zmian final_position CategoryOverallResult do zapisania.")

    print(f"--- [DEBUG OVERALL - {category.id}] Koniec update_overall_results_for_category ---")

@transaction.atomic # Upewnij się, że ten dekorator jest obecny
def update_overall_results_for_player(player: Player) -> None:
    """
    Aktualizuje wyniki dla WSZYSTKICH kategorii gracza.
    """
    if not hasattr(player, "categories"):
        print(f"Gracz {player.id} ({player}) nie ma atrybutu 'categories'. Pomijam.")
        return

    try:
        # Pobierz kategorie gracza BEZ błędnego prefetch_related
        # ZMIANA TUTAJ vvv
        categories = list(player.categories.all())
        # KONIEC ZMIANY ^^^
    except Exception as e_fetch:
        # Zaktualizowano komunikat błędu
        print(f"BŁĄD pobierania kategorii dla gracza {player.id} ({player}): {e_fetch}")
        traceback.print_exc() # Dodaj traceback dla lepszej diagnostyki
        return # Zakończ funkcję, jeśli nie udało się pobrać kategorii

    if not categories:
        print(f"Gracz {player.id} ({player}) nie ma przypisanych kategorii. Pomijam.")
        # Rozważ usunięcie starych wyników Overall dla tego gracza, jeśli taka jest logika
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
        print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id} ({player}): {e}")
        traceback.print_exc() # Zawsze loguj pełny traceback przy krytycznych błędach


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
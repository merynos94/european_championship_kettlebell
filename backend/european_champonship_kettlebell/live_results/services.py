epsilon = 1e-6
import traceback

from django.db import transaction
from django.db.models import Case, F, FloatField, Value, When
from django.db.models.functions import Greatest

from .models import Category, Player
# Updated constants import
from .models.constants import KB_SQUAT, ONE_KB_PRESS, SNATCH, TGU, TWO_KB_PRESS # PISTOL_SQUAT, SEE_SAW_PRESS removed
# Updated results import
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    OverallResult,
    # PistolSquatResult, # Commented out
    # SeeSawPressResult, # Commented out
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)

# Updated DISCIPLINE_MODELS_MAP
DISCIPLINE_MODELS_MAP = {
    SNATCH: SnatchResult,
    TGU: TGUResult,
    # SEE_SAW_PRESS: SeeSawPressResult, # Commented out
    KB_SQUAT: KBSquatResult,
    # PISTOL_SQUAT: PistolSquatResult, # Commented out
    ONE_KB_PRESS: OneKettlebellPressResult,
    TWO_KB_PRESS: TwoKettlebellPressResult,
}

# Updated DEFAULT_RESULT_VALUES
DEFAULT_RESULT_VALUES = {
    SNATCH: {"kettlebell_weight": 0, "repetitions": 0},
    TGU: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
    # PISTOL_SQUAT: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0}, # Commented out
    ONE_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0},
    # SEE_SAW_PRESS: { # Commented out
    #     "result_left_1": 0.0,
    #     "result_right_1": 0.0,
    #     "result_left_2": 0.0,
    #     "result_right_2": 0.0,
    #     "result_left_3": 0.0,
    #     "result_right_3": 0.0,
    # },
    KB_SQUAT: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0}, # Updated for SingleAttempt
    TWO_KB_PRESS: {"result_1": 0.0, "result_2": 0.0, "result_3": 0.0}, # Updated for SingleAttempt
}

# Wklej ten kod do pliku services.py
# Upewnij się, że importy na górze pliku są kompletne

# --- Nowa funkcja pomocnicza ---
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

    # Pobierz ID graczy tylko dla tej kategorii
    players_in_category_ids = list(Player.objects.filter(categories=category).values_list("id", flat=True))
    if player.id not in players_in_category_ids:
        print(f"    DEBUG (get_rank): Gracz {player.id} nie należy do kategorii {category.id}")
        return None # Gracz nie jest w tej kategorii

    # Pobierz wyniki tylko dla graczy z tej kategorii
    results_qs = model.objects.filter(player_id__in=players_in_category_ids).select_related('player')

    # Logika sortowania i adnotacji (musi być zgodna z update_discipline_positions)
    ordering_logic = {
        SNATCH: "-calculated_snatch_score",
        TGU: "-tgu_bw_ratio",
        ONE_KB_PRESS: "-okbp_bw_ratio",
        KB_SQUAT: "-kbs_bw_ratio",
        TWO_KB_PRESS: "-tkbp_bw_ratio",
    }
    order_by_field = ordering_logic.get(discipline)
    if not order_by_field:
        print(f"    DEBUG (get_rank): Brak logiki sortowania dla {discipline}")
        return None

    # Zastosuj adnotacje do obliczenia wyniku sortującego
    annotated_qs = results_qs
    annotation_field_name = None

    # --- POCZĄTEK: Logika Adnotacji (skopiowana/dostosowana z update_discipline_positions) ---
    # WAŻNE: Upewnij się, że modele KBSquatResult i TwoKettlebellPressResult mają pola result_1/2/3/max_result_val!
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
                # Zakładamy, że model ma result_1, result_2, result_3
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
                # Zakładamy, że model ma result_1, result_2, result_3
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
             return None # Brak logiki adnotacji
    # --- KONIEC: Logika Adnotacji ---

        if not annotation_field_name:
             print(f"    DEBUG (get_rank) ERROR: Nie udało się ustalić pola adnotacji dla {discipline}.")
             return None

        # Posortuj wyniki
        ordered_results = annotated_qs.order_by(order_by_field, "player__surname", "player__name")

        # Znajdź ranking dla konkretnego gracza
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

            # Logika remisu (bez epsilon, używa bezpośredniego porównania)
            # UWAGA: Ryzykowne dla float!
            is_tie = False
            if last_score is not None:
                if score == last_score:
                    is_tie = True

            calculated_rank_for_this_iteration = 0
            if not is_tie: # Nie ma remisu lub pierwszy element
                calculated_rank_for_this_iteration = rank_counter
                last_score = score
                tie_start_rank = rank_counter
            else: # Jest remis
                calculated_rank_for_this_iteration = tie_start_rank

            # Sprawdź, czy to nasz szukany gracz
            if result.player_id == player.id:
                player_rank = calculated_rank_for_this_iteration
                print(f"    DEBUG (get_rank): Znaleziono ranking {player_rank} dla gracza {player.id} w {discipline} (kat: {category.id})")
                break # Znaleziono, przerwij pętlę

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
    # Prefetch related normalny, OverallResult jest pobierany w pętli
    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        "snatch_result",
        "tgu_result",
        "kb_squat_one_result", # Upewnij się, że related_name jest poprawny
        "one_kettlebell_press_result",
        "two_kettlebell_press_one_result", # Upewnij się, że related_name jest poprawny
        # "overallresult", # Niepotrzebne, bo get_or_create
    )
    if not players_in_category.exists():
        print(f"Brak graczy w kategorii {category.id}. Pomijam obliczanie wyników ogólnych.")
        return

    print(f"Aktualizacja wyników ogólnych dla kategorii: {category.name} ({category.id})")
    disciplines_in_category = category.get_disciplines()
    overall_updates = []
    final_pos_updates = [] # Lista do aktualizacji final_position

    # Mapowania nazw (sprawdź related_name dla KBS i TKBP!)
    discipline_related_names = {
        SNATCH: "snatch_result",
        TGU: "tgu_result",
        KB_SQUAT: "kb_squat_one_result", # Sprawdź!
        ONE_KB_PRESS: "one_kettlebell_press_result",
        TWO_KB_PRESS: "two_kettlebell_press_one_result", # Sprawdź!
    }
    overall_points_fields = {
        SNATCH: "snatch_points",
        TGU: "tgu_points",
        KB_SQUAT: "kb_squat_points",
        ONE_KB_PRESS: "one_kb_press_points",
        TWO_KB_PRESS: "two_kb_press_points",
    }

    # --- Pętla po graczach w kategorii ---
    for player in players_in_category:
        overall_result, created_overall = OverallResult.objects.get_or_create(player=player)
        if created_overall:
            print(f"  Stworzono brakujący rekord OverallResult dla gracza {player.id}")

        changed = False # Flaga czy OverallResult gracza wymaga zapisu

        # 1. Wyczyść stare punkty dyscyplin (na wszelki wypadek)
        for field_name in overall_points_fields.values():
            if getattr(overall_result, field_name, None) is not None:
                setattr(overall_result, field_name, None)
                changed = True

        # 2. Ustaw punkty Tiebreak
        new_tiebreak_points = -0.5 if player.tiebreak else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True

        # 3. Oblicz i przypisz punkty dla każdej dyscypliny w kategorii
        print(f"  Obliczanie punktów dla gracza: {player.id} ({player})")
        for disc_const in disciplines_in_category:
            points_field = overall_points_fields.get(disc_const)
            related_name = discipline_related_names.get(disc_const) # Potrzebne? Niekoniecznie tutaj

            if not points_field or not related_name:
                print(f"    OSTRZEŻENIE: Brak konfiguracji punktów/related_name dla dyscypliny {disc_const}")
                continue # Pomiń tę dyscyplinę

            # --- ZMIANA: Użyj nowej funkcji do pobrania rankingu ---
            calculated_rank = get_player_rank_in_discipline(player, disc_const, category)
            new_points = float(calculated_rank) if calculated_rank is not None else None
            # ------------------------------------------------------

            print(f"    Dyscyplina: {disc_const}, Obliczony Rank: {calculated_rank}, Przypisane Punkty: {new_points}")

            # Porównaj i zaktualizuj punkty w OverallResult
            if getattr(overall_result, points_field, None) != new_points:
                setattr(overall_result, points_field, new_points)
                changed = True

        # 4. Oblicz sumę punktów
        old_total_points = overall_result.total_points
        overall_result.calculate_total_points() # Sumuje pola *_points i tiebreak
        print(f"    Obliczono total_points: {overall_result.total_points} (poprzednio: {old_total_points})")
        if old_total_points != overall_result.total_points:
            changed = True

        # 5. Dodaj do listy do aktualizacji, jeśli były zmiany
        if changed or created_overall:
            overall_updates.append(overall_result)

    # --- Koniec pętli po graczach ---

    # 6. Zapisz zmiany w punktach (bulk_update)
    if overall_updates:
        update_fields = list(overall_points_fields.values()) + ["tiebreak_points", "total_points"]
        try:
            updated_points_count = OverallResult.objects.bulk_update(overall_updates, update_fields)
            print(f"  Zaktualizowano punkty OverallResult dla {updated_points_count} graczy.")
        except Exception as e_bulk_overall:
            print(f"  BŁĄD bulk_update punktów OverallResult w kategorii {category.id}: {e_bulk_overall}")
            traceback.print_exc()
    else:
         print("  Brak zmian punktów OverallResult do zapisania.")


    # 7. Oblicz i zaktualizuj MIEJSCA KOŃCOWE (final_position)
    # Pobierz ponownie OverallResult posortowane wg zasad rankingu generalnego
    # Używamy -total_points, bo None ma być na końcu, a niższa suma jest lepsza. Sortujemy None na końcu.
    # Użyjemy warunkowego sortowania: najpierw wg tego czy total_points jest null, potem wg wartości
    final_results = OverallResult.objects.filter(player__in=players_in_category).annotate(
        total_points_is_null=Case(When(total_points__isnull=True, then=Value(1)), default=Value(0), output_field=models.IntegerField())
    ).order_by(
        'total_points_is_null', # Najpierw ci co mają wynik (0), potem ci co nie mają (1)
        "total_points",         # Potem rosnąco wg punktów (mniej = lepiej)
        "player__surname",      # Potem wg nazwiska
        "player__name"
    )

    current_final_pos = 0
    last_total_points = None
    final_rank_counter = 0
    # tie_start_rank_final = 1 # Do poprawnej obsługi remisów w final_position

    print(f"\n  Obliczanie Miejsc Końcowych (final_position) dla {final_results.count()} wyników...")
    for result in final_results:
        final_rank_counter += 1
        current_total_points = result.total_points # Może być None

        # Logika remisu dla final_position (porównujemy total_points)
        # Traktujemy None jako różne od wszystkiego innego i od siebie nawzajem
        is_tie_final = False
        if current_total_points is not None and last_total_points is not None:
            # Użyjemy bezpośredniego porównania (zakładając, że suma jest w miarę stabilna)
            if current_total_points == last_total_points:
                 is_tie_final = True
        # Jeśli obecny lub poprzedni to None, to nie ma remisu (chyba że oba są None, co jest mało prawdopodobne w rankingu)

        calculated_final_pos_for_iteration = 0
        if not is_tie_final: # Nie ma remisu lub pierwszy rekord
            calculated_final_pos_for_iteration = final_rank_counter
            last_total_points = current_total_points
            # tie_start_rank_final = final_rank_counter # Resetuj rangę startową remisu
        else: # Jest remis
            # Tutaj powinniśmy użyć rangi startowej remisu, ale uproszczona logika rank_counter
            # dla final_position może być wystarczająca, jeśli remisy są rzadkie LUB jeśli
            # chcemy po prostu 1, 2, 3, 3, 5. Aby uzyskać 1, 2, 3, 3, 4 musimy śledzić tie_start_rank_final
            # Dla uproszczenia na razie zostawmy rank_counter, co da 1, 2, 3, 4, 5 nawet przy remisie na 3/4 miejscu
            # Poprawka: Użyjmy poprawnej logiki remisu jak w dyscyplinach
             calculated_final_pos_for_iteration = current_final_pos # Użyj ostatnio przypisanego miejsca

        # AKTUALIZACJA: Poprawiona logika final_position z obsługą remisów (1,2,3,3,5)
        if not is_tie_final:
            current_final_pos = final_rank_counter # Nowe miejsce to licznik
            last_total_points = current_total_points
        # Jeśli jest remis, current_final_pos pozostaje bez zmian


        # Porównaj i dodaj do aktualizacji, jeśli konieczne
        if result.final_position != current_final_pos or result.final_position is None:
            result.final_position = current_final_pos
            final_pos_updates.append(result)
            print(f"    Aktualizacja final_position dla {result.player_id}: {current_final_pos}")


    # 8. Zapisz zmiany w miejscach końcowych (bulk_update)
    if final_pos_updates:
        try:
            updated_pos_count = OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  Zaktualizowano final_position OverallResult dla {updated_pos_count} graczy.")
        except Exception as e_bulk_final:
            print(f"  BŁĄD bulk_update final_position OverallResult w kategorii {category.id}: {e_bulk_final}")
            traceback.print_exc()
    else:
        print("  Brak zmian final_position OverallResult do zapisania.")


# --- Funkcja update_overall_results_for_player ---
# Pozostaje bez zmian, nadal wywołuje powyższe funkcje w pętli po kategoriach
@transaction.atomic # Dodajemy transakcję na całą operację dla gracza
def update_overall_results_for_player(player: Player) -> None:
    """
    Aktualizuje pozycje w dyscyplinach i wyniki ogólne dla WSZYSTKICH kategorii,
    do których należy gracz. Obejmuje całość transakcją atomową.
    """
    # Sprawdzenia początkowe
    if not hasattr(player, "categories"):
        print(f"Obiekt gracza {player.id} nie ma atrybutu 'categories'. Pomijam aktualizację.")
        return

    # Pobierz kategorie w ramach transakcji, żeby widzieć spójny stan
    categories = list(player.categories.all())

    if not categories:
        print(f"Gracz {player.id} nie ma przypisanych kategorii. Pomijam aktualizację overall.")
        # Rozważ usunięcie OverallResult jeśli gracz nie ma kategorii?
        # OverallResult.objects.filter(player=player).delete()
        return

    print(f"=== Rozpoczynam pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    try:
        # Pętla po kategoriach gracza
        print(f"Aktualizuję wyniki dla gracza {player.id} w kategoriach: {[c.name for c in categories]}")
        for category in categories:
            print(f"\n--- Aktualizacja dla Kategorii: {category.name} ({category.id}) ---")
            # 1. Zaktualizuj pozycje WEWNĄTRZ tej kategorii (nadal zapisuje pozycję na głównym obiekcie wyniku!)
            # To jest OK, bo zaraz odczytamy ranking DLA TEJ KATEGORII poniżej
            update_discipline_positions(category) # Ta funkcja ma teraz głównie efekt uboczny w postaci logów

            # 2. Zaktualizuj OverallResult DLA TEJ KATEGORII, używając świeżo obliczonych rankingów
            update_overall_results_for_category(category) # Ta funkcja teraz polega na get_player_rank_in_discipline

        print(f"=== Zakończono pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    except Exception as e:
        print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id}: {e}")
        traceback.print_exc()
        # Transakcja zostanie automatycznie wycofana dzięki @transaction.atomic

# --- Pozostałe funkcje (np. create_default_results_for_player_categories) ---
# Pozostają bez zmian w stosunku do wersji z pliku services.py, który mi dostarczyłeś.
# Upewnij się, że są obecne w Twoim pliku.

@transaction.atomic
def create_default_results_for_player_categories(player: Player, category_pks: set[int]):
    """
    Creates default (zeroed) result entries for a player in disciplines
    associated with newly assigned categories. Uses get_or_create to avoid duplicates.
    Returns True if any new record was created, False otherwise.
    """
    if not category_pks:
        return False

    created_new = False

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
            if discipline_key in DISCIPLINE_MODELS_MAP: # Uses updated map
                model_class = DISCIPLINE_MODELS_MAP[discipline_key]
                defaults = DEFAULT_RESULT_VALUES.get(discipline_key, {}).copy() # Uses updated defaults

                obj, created = model_class.objects.get_or_create(player=player, defaults=defaults)
                if created:
                    created_new = True
                    print(f"    + Stworzono domyślny rekord {model_class.__name__} dla gracza {player.id}")
            else:
                print(
                    f"    ! OSTRZEŻENIE: Nie znaleziono modelu dla dyscypliny '{discipline_key}' w kategorii {category.id}"
                )

    return created_new


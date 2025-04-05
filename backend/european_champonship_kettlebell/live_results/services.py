# live_results/services.py
epsilon = 1e-6
import traceback
from django.db import transaction
from django.db.models import Case, F, FloatField, Value, When
from django.db.models.functions import Greatest
from django.utils.translation import gettext_lazy as _

# --- Importy Modeli i Stałych ---
# Zakładamy, że modele są w podkatalogu 'models' aplikacji 'live_results'
# oraz że __init__.py w models/ eksportuje Category i Player
from .models import Category, Player
# Zakładamy, że __init__.py w models/results/ eksportuje te modele
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
# Importuj stałe dyscyplin
from .models.constants import (
    SNATCH, TGU, SEE_SAW_PRESS, KB_SQUAT, PISTOL_SQUAT,
    ONE_KB_PRESS, TWO_KB_PRESS # Usunięto AVAILABLE_DISCIPLINES jeśli nie jest używane bezpośrednio tutaj
)

# --- Mapy Konfiguracyjne ---

# Mapa modeli dyscyplin
DISCIPLINE_MODELS_MAP = {
    SNATCH: SnatchResult,
    TGU: TGUResult,
    SEE_SAW_PRESS: SeeSawPressResult,
    KB_SQUAT: KBSquatResult,
    PISTOL_SQUAT: PistolSquatResult,
    ONE_KB_PRESS: OneKettlebellPressResult,
    TWO_KB_PRESS: TwoKettlebellPressResult,
}

# Mapa domyślnych wartości dla każdego modelu wyniku przy tworzeniu
DEFAULT_RESULT_VALUES = {
    SNATCH: {'kettlebell_weight': 0, 'repetitions': 0},
    TGU: {'result_1': 0.0, 'result_2': 0.0, 'result_3': 0.0},
    PISTOL_SQUAT: {'result_1': 0.0, 'result_2': 0.0, 'result_3': 0.0},
    ONE_KB_PRESS: {'result_1': 0.0, 'result_2': 0.0, 'result_3': 0.0},
    SEE_SAW_PRESS: {
        'result_left_1': 0.0, 'result_right_1': 0.0,
        'result_left_2': 0.0, 'result_right_2': 0.0,
        'result_left_3': 0.0, 'result_right_3': 0.0,
    },
    KB_SQUAT: {
        'result_left_1': 0.0, 'result_right_1': 0.0,
        'result_left_2': 0.0, 'result_right_2': 0.0,
        'result_left_3': 0.0, 'result_right_3': 0.0,
    },
    TWO_KB_PRESS: {
        'result_left_1': 0.0, 'result_right_1': 0.0,
        'result_left_2': 0.0, 'result_right_2': 0.0,
        'result_left_3': 0.0, 'result_right_3': 0.0,
    },
}

# --- Logika Obliczania Pozycji i Wyników ---

# Ta funkcja pozostaje bez zmian - jej logika rankingu poprawnie obsłuży wyniki 0.0
def update_discipline_positions(category: Category) -> None:
    """Calculates and updates positions for players within a category for each relevant discipline."""
    # Import lokalny, aby uniknąć problemów z zależnościami cyklicznymi, jeśli services.py jest importowany w models.py
    # from .models import Player - już zaimportowano na górze

    players_in_category = Player.objects.filter(categories=category).only("id", "weight", "surname", "name")
    if not players_in_category.exists():
        print(f"Brak graczy w kategorii {category.id}. Pomijam obliczanie pozycji dyscyplin.")
        return

    player_ids = list(players_in_category.values_list("id", flat=True))

    disciplines = category.get_disciplines()
    if not disciplines:
        print(f"Kategoria {category.id} nie ma zdefiniowanych dyscyplin. Pomijam obliczanie pozycji.")
        return

    # Używamy globalnej mapy
    # discipline_models_map = DISCIPLINE_MODELS_MAP

    # Logika sortowania dla każdej dyscypliny
    ordering_logic = {
        SNATCH: "-calculated_snatch_score", # Sortowanie po adnotacji
        TGU: "-tgu_bw_ratio",
        PISTOL_SQUAT: "-pistol_bw_ratio",
        ONE_KB_PRESS: "-okbp_bw_ratio",
        SEE_SAW_PRESS: "-ssp_bw_ratio",
        KB_SQUAT: "-kbs_bw_ratio",
        TWO_KB_PRESS: "-tkbp_bw_ratio",
    }

    epsilon = 1e-6 # Mała wartość do porównywania floatów

    print(f"Aktualizacja pozycji w dyscyplinach dla kategorii: {category.name} ({category.id})")
    for discipline in disciplines:
        if discipline not in DISCIPLINE_MODELS_MAP:
            print(f"  OSTRZEŻENIE: Pomijam nieznaną dyscyplinę '{discipline}' w kategorii {category.id}")
            continue

        model = DISCIPLINE_MODELS_MAP[discipline]
        order_by_field = ordering_logic.get(discipline)
        if not order_by_field:
            print(f"  OSTRZEŻENIE: Brak logiki sortowania dla dyscypliny '{discipline}'. Pomijam.")
            continue

        print(f"  Przetwarzanie dyscypliny: {discipline}")
        # Pobieramy wyniki tylko dla graczy z tej kategorii
        results_qs = model.objects.select_related("player").filter(player_id__in=player_ids)

        # --- Adnotacje do sortowania ---
        # (Logika adnotacji pozostaje taka sama jak w oryginalnym kodzie)
        if discipline == SNATCH:
              results_qs = results_qs.annotate(
                  calculated_snatch_score=Case(
                      When(kettlebell_weight__gt=0, repetitions__gt=0, then=F('kettlebell_weight') * F('repetitions')),
                      default=Value(0.0), output_field=FloatField()
                  )
              )
        elif discipline == TGU:
            results_qs = results_qs.annotate(
                max_tgu_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField()) # Zapewnienie, że porównujemy z floatem
            ).annotate(
                tgu_bw_ratio=Case( When(player__weight__gt=0, max_tgu_result__gt=0, then=F("max_tgu_result") / F("player__weight")), default=Value(0.0), output_field=FloatField() )
            )
        elif discipline == PISTOL_SQUAT:
             results_qs = results_qs.annotate(
                max_pistol_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                pistol_bw_ratio=Case( When(player__weight__gt=0, max_pistol_result__gt=0, then=F("max_pistol_result") / F("player__weight")), default=Value(0.0), output_field=FloatField() )
            )
        elif discipline == ONE_KB_PRESS:
            results_qs = results_qs.annotate(
                max_okbp_result=Greatest(F("result_1"), F("result_2"), F("result_3"), Value(0.0), output_field=FloatField())
            ).annotate(
                okbp_bw_ratio=Case( When(player__weight__gt=0, max_okbp_result__gt=0, then=F("max_okbp_result") / F("player__weight")), default=Value(0.0), output_field=FloatField() )
            )
        elif discipline == SEE_SAW_PRESS:
             results_qs = results_qs.annotate(
                    ssp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")), default=Value(0.0), output_field=FloatField()),
                    ssp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")), default=Value(0.0), output_field=FloatField()),
                    ssp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")), default=Value(0.0), output_field=FloatField()),
                ).annotate(max_ssp_score=Greatest("ssp_score_1", "ssp_score_2", "ssp_score_3", Value(0.0), output_field=FloatField()) # Dodano Value(0.0)
                ).annotate(
                    ssp_bw_ratio=Case(When(player__weight__gt=0, max_ssp_score__gt=0, then=F("max_ssp_score") / F("player__weight")), default=Value(0.0), output_field=FloatField())
                )
        elif discipline == KB_SQUAT:
            results_qs = results_qs.annotate(
                    kbs_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")), default=Value(0.0), output_field=FloatField()),
                    kbs_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")), default=Value(0.0), output_field=FloatField()),
                    kbs_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")), default=Value(0.0), output_field=FloatField()),
                ).annotate(max_kbs_score=Greatest("kbs_score_1", "kbs_score_2", "kbs_score_3", Value(0.0), output_field=FloatField()) # Dodano Value(0.0)
                ).annotate(
                    kbs_bw_ratio=Case(When(player__weight__gt=0, max_kbs_score__gt=0, then=F("max_kbs_score") / F("player__weight")), default=Value(0.0), output_field=FloatField())
                )
        elif discipline == TWO_KB_PRESS:
            results_qs = results_qs.annotate(
                    tkbp_score_1=Case(When(result_left_1__gt=0, result_right_1__gt=0, then=F("result_left_1") + F("result_right_1")), default=Value(0.0), output_field=FloatField()),
                    tkbp_score_2=Case(When(result_left_2__gt=0, result_right_2__gt=0, then=F("result_left_2") + F("result_right_2")), default=Value(0.0), output_field=FloatField()),
                    tkbp_score_3=Case(When(result_left_3__gt=0, result_right_3__gt=0, then=F("result_left_3") + F("result_right_3")), default=Value(0.0), output_field=FloatField()),
                ).annotate(max_tkbp_score=Greatest("tkbp_score_1", "tkbp_score_2", "tkbp_score_3", Value(0.0), output_field=FloatField()) # Dodano Value(0.0)
                ).annotate(
                    tkbp_bw_ratio=Case(When(player__weight__gt=0, max_tkbp_score__gt=0, then=F("max_tkbp_score") / F("player__weight")), default=Value(0.0), output_field=FloatField())
                )
        # --- Koniec Adnotacji ---

        # Sortowanie wg obliczonego pola i nazwiska/imienia jako tie-breaker
        ordered_results = results_qs.order_by(order_by_field, "player__surname", "player__name")

        updates = []
        current_pos = 0
        last_score = None # Używane do śledzenia zmiany wyniku dla pozycji ex aequo
        rank_counter = 0 # Licznik do określenia numeru pozycji

        # Iteracja i przypisanie pozycji
        for result in ordered_results:
            rank_counter += 1
            score = 0.0
            try:
                # Pobieramy odpowiednią *zaadnotowaną* wartość do rankingu
                if discipline == SNATCH: score = result.calculated_snatch_score
                elif discipline == TGU: score = result.tgu_bw_ratio
                elif discipline == PISTOL_SQUAT: score = result.pistol_bw_ratio
                elif discipline == ONE_KB_PRESS: score = result.okbp_bw_ratio
                elif discipline == SEE_SAW_PRESS: score = result.ssp_bw_ratio
                elif discipline == KB_SQUAT: score = result.kbs_bw_ratio
                elif discipline == TWO_KB_PRESS: score = result.tkbp_bw_ratio
                score = float(score or 0.0) # Upewniamy się, że to float
            except (AttributeError, TypeError, ValueError):
                score = 0.0 # Domyślnie 0 jeśli coś pójdzie nie tak

            # Sprawdzamy, czy wynik się zmienił w stosunku do poprzedniego gracza
            if last_score is None or abs(score - last_score) > epsilon:
                current_pos = rank_counter # Jeśli tak, aktualna pozycja = licznik
            # Jeśli wynik jest taki sam, current_pos pozostaje niezmienione (ex aequo)
            last_score = score # Zapisujemy obecny wynik do porównania w następnej iteracji

            # Dodajemy do listy aktualizacji tylko jeśli pozycja się zmieniła
            if result.position != current_pos:
                result.position = current_pos
                updates.append(result)

        # Aktualizacja masowa pozycji w bazie danych
        if updates:
            try:
                updated_count = model.objects.bulk_update(updates, ["position"])
                print(f"    Zaktualizowano pozycje dla {updated_count} rekordów w {discipline}.")
            except Exception as e_bulk:
                print(f"    BŁĄD bulk_update pozycji dla {discipline} w kategorii {category.id}: {e_bulk}")
                traceback.print_exc()
        else:
             print(f"    Brak zmian pozycji do zapisania dla {discipline}.")


# Ta funkcja pozostaje bez zmian - korzysta z obliczonych pozycji
def update_overall_results_for_category(category: Category) -> None:
    """Calculates and updates overall points and final positions for players within a category."""
    # Import lokalny
    # from .models import Player - już zaimportowano

    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        "snatch_result", "tgu_result", "pistol_squat_result",
        "see_saw_press_result", "kb_squat_result", "one_kettlebell_press_result",
        "two_kettlebell_press_result", "overallresult", # Prefetch OverallResult
    )
    if not players_in_category.exists():
        print(f"Brak graczy w kategorii {category.id}. Pomijam obliczanie wyników ogólnych.")
        return

    print(f"Aktualizacja wyników ogólnych dla kategorii: {category.name} ({category.id})")
    disciplines_in_category = category.get_disciplines()
    overall_updates = [] # Lista obiektów OverallResult do aktualizacji punktów
    final_pos_updates = [] # Lista obiektów OverallResult do aktualizacji final_position

    # Mapowanie stałych na nazwy related_name i pola punktowe w OverallResult
    discipline_related_names = {
        SNATCH: "snatch_result", TGU: "tgu_result", PISTOL_SQUAT: "pistol_squat_result",
        SEE_SAW_PRESS: "see_saw_press_result", KB_SQUAT: "kb_squat_result",
        ONE_KB_PRESS: "one_kettlebell_press_result", TWO_KB_PRESS: "two_kettlebell_press_result",
    }
    overall_points_fields = {
        SNATCH: "snatch_points", TGU: "tgu_points", PISTOL_SQUAT: "pistol_squat_points",
        SEE_SAW_PRESS: "see_saw_press_points", KB_SQUAT: "kb_squat_points",
        ONE_KB_PRESS: "one_kb_press_points", TWO_KB_PRESS: "two_kb_press_points",
    }

    # 1. Oblicz punkty dla każdego gracza na podstawie pozycji w dyscyplinach
    for player in players_in_category:
        # Używamy get_or_create, aby upewnić się, że rekord OverallResult istnieje
        overall_result, created_overall = OverallResult.objects.get_or_create(player=player)
        if created_overall:
             print(f"  Stworzono brakujący rekord OverallResult dla gracza {player.id}")

        # Resetuj punkty dyscyplin przed obliczeniem
        changed = False # Flaga śledząca czy coś się zmieniło
        for field_name in overall_points_fields.values():
             if getattr(overall_result, field_name, None) is not None:
                 setattr(overall_result, field_name, None)
                 changed = True

        # Ustaw punkty tiebreak
        new_tiebreak_points = -0.5 if player.tiebreak else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True

        # Przypisz punkty na podstawie pozycji w dyscyplinach z tej kategorii
        for disc_const, related_name in discipline_related_names.items():
            # Sprawdź, czy dyscyplina jest w tej kategorii
            if disc_const in disciplines_in_category:
                result_obj = getattr(player, related_name, None)
                points_field = overall_points_fields[disc_const]
                new_points = None
                # Sprawdź czy jest wynik i czy ma obliczoną pozycję
                if result_obj and hasattr(result_obj, 'position') and result_obj.position is not None:
                    new_points = float(result_obj.position)

                # Aktualizuj tylko jeśli wartość się zmieniła
                if getattr(overall_result, points_field, None) != new_points:
                    setattr(overall_result, points_field, new_points)
                    changed = True
            # Jeśli dyscyplina nie jest w kategorii, upewnij się, że punkty są None (powinno być z resetu wyżej)
            else:
                points_field = overall_points_fields.get(disc_const)
                if points_field and getattr(overall_result, points_field, None) is not None:
                     setattr(overall_result, points_field, None)
                     changed = True


        # Oblicz sumę punktów (zakładając, że metoda istnieje w modelu OverallResult)
        old_total_points = overall_result.total_points
        overall_result.calculate_total_points()
        if old_total_points != overall_result.total_points:
             changed = True

        # Dodaj do listy aktualizacji tylko jeśli coś się zmieniło
        if changed or created_overall: # Dodajemy też nowo utworzone
            overall_updates.append(overall_result)

    # 2. Zapisz zaktualizowane punkty masowo
    if overall_updates:
        update_fields = list(overall_points_fields.values()) + ["tiebreak_points", "total_points"]
        try:
            updated_points_count = OverallResult.objects.bulk_update(overall_updates, update_fields)
            print(f"  Zaktualizowano punkty OverallResult dla {updated_points_count} graczy.")
        except Exception as e_bulk_overall:
            print(f"  BŁĄD bulk_update punktów OverallResult w kategorii {category.id}: {e_bulk_overall}")
            traceback.print_exc()
            # W razie błędu, kontynuujemy do obliczania pozycji, ale wyniki mogą być niekompletne

    # 3. Oblicz końcowe pozycje na podstawie zaktualizowanych total_points
    # Pobieramy ponownie wyniki, aby mieć pewność, że pracujemy na zapisanych danych
    final_results = OverallResult.objects.filter(player__categories=category).order_by(
        # Sortuj wg sumy punktów (NULLs last domyślnie w PostgreSQL, co jest OK - bez wyniku są ostatni)
        # Następnie wg nazwiska/imienia jako tie-breaker dla tej samej sumy punktów
        "total_points", "player__surname", "player__name"
    )

    current_final_pos = 0
    last_total_points = None
    final_rank_counter = 0

    for result in final_results:
        final_rank_counter += 1
        current_total_points = result.total_points # Może być None

        # Sprawdzamy zmianę wyniku (obsługując None)
        # Pozycja zmienia się jeśli:
        # - To pierwszy zawodnik (last_total_points is None)
        # - Obecny wynik jest różny od poprzedniego ORAZ oba nie są None
        # - Jeden z wyników jest None, a drugi nie (osoba bez wyniku jest za osobą z wynikiem)
        should_update_pos = False
        if last_total_points is None: # Pierwszy zawodnik
             should_update_pos = True
        elif current_total_points is None and last_total_points is not None: # Zmiana z wyniku na brak wyniku
             should_update_pos = True
        elif current_total_points is not None and last_total_points is None: # Zmiana z braku wyniku na wynik
             should_update_pos = True
        elif current_total_points is not None and last_total_points is not None and abs(current_total_points - last_total_points) > epsilon: # Zmiana wyniku
             should_update_pos = True
        # Jeśli current_total_points == last_total_points (wliczając None == None), pozycja się nie zmienia

        if should_update_pos:
            current_final_pos = final_rank_counter
        last_total_points = current_total_points

        # Dodajemy do aktualizacji tylko jeśli pozycja się zmieniła
        if result.final_position != current_final_pos:
            result.final_position = current_final_pos
            final_pos_updates.append(result)

    # 4. Zapisz zaktualizowane końcowe pozycje masowo
    if final_pos_updates:
        try:
            updated_pos_count = OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  Zaktualizowano final_position OverallResult dla {updated_pos_count} graczy.")
        except Exception as e_bulk_final:
             print(f"  BŁĄD bulk_update final_position OverallResult w kategorii {category.id}: {e_bulk_final}")
             traceback.print_exc()
    else:
         print(f"  Brak zmian final_position OverallResult do zapisania.")


# --- NOWA FUNKCJA do tworzenia domyślnych rekordów ---
@transaction.atomic # Używamy transakcji dla spójności
def create_default_results_for_player_categories(player: Player, category_pks: set[int]):
    """
    Creates default (zeroed) result entries for a player in disciplines
    associated with newly assigned categories.
    Uses get_or_create to avoid duplicates.
    Returns True if any new record was created, False otherwise.
    """
    if not category_pks:
        return False # Nic do zrobienia

    created_new = False # Flaga śledząca, czy cokolwiek zostało stworzone

    # Pobieramy tylko te kategorie, które faktycznie zostały dodane
    categories_to_process = Category.objects.filter(pk__in=category_pks)
    print(f"Tworzenie domyślnych wyników dla gracza {player.id} w kategoriach: {[c.name for c in categories_to_process]}")

    for category in categories_to_process:
        disciplines_in_category = category.get_disciplines()
        if not disciplines_in_category:
            print(f"  Kategoria {category.name} nie ma dyscyplin.")
            continue

        print(f"  Przetwarzanie kategorii: {category.name}")
        for discipline_key in disciplines_in_category:
            if discipline_key in DISCIPLINE_MODELS_MAP:
                model_class = DISCIPLINE_MODELS_MAP[discipline_key]
                # Pobieramy domyślne wartości dla tego modelu
                # Używamy kopii, aby uniknąć modyfikacji oryginalnego słownika
                defaults = DEFAULT_RESULT_VALUES.get(discipline_key, {}).copy()

                # Używamy get_or_create, aby stworzyć rekord tylko jeśli nie istnieje
                # Kluczem jest 'player', reszta idzie do 'defaults'
                obj, created = model_class.objects.get_or_create(
                    player=player,
                    defaults=defaults
                )
                if created:
                    created_new = True
                    print(f"    + Stworzono domyślny rekord {model_class.__name__} dla gracza {player.id}")
                # else:
                #    print(f"    - Rekord {model_class.__name__} dla gracza {player.id} już istniał.")
            else:
                 print(f"    ! OSTRZEŻENIE: Nie znaleziono modelu dla dyscypliny '{discipline_key}' w kategorii {category.id}")

    return created_new # Zwraca True jeśli stworzono przynajmniej jeden nowy rekord


# --- Główna funkcja aktualizująca dla gracza ---
def update_overall_results_for_player(player: Player) -> None:
    """
    Updates discipline positions and overall results for ALL categories
    a player belongs to. Wrapped in a transaction.
    """
    # Sprawdźmy najpierw czy obiekt player ma managera kategorii
    if not hasattr(player, 'categories'):
         print(f"Obiekt gracza {player.id} nie ma atrybutu 'categories'. Pomijam aktualizację.")
         return
    # Sprawdźmy, czy gracz ma przypisane jakiekolwiek kategorie
    if not player.categories.exists():
        print(f"Gracz {player.id} nie ma przypisanych kategorii. Pomijam aktualizację overall.")
        return

    print(f"=== Rozpoczynam pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    # Używamy transaction.atomic, aby zapewnić spójność całego procesu aktualizacji
    try:
        with transaction.atomic():
            # Pobieramy listę kategorii gracza raz, aby uniknąć wielokrotnych zapytań
            categories = list(player.categories.all())
            if not categories:
                print(f"Gracz {player.id} nie ma kategorii po pobraniu listy. Kończę.")
                return

            print(f"Aktualizuję wyniki dla gracza {player.id} w kategoriach: {[c.name for c in categories]}")
            for category in categories:
                # Najpierw aktualizujemy pozycje we wszystkich dyscyplinach DLA CAŁEJ KATEGORII
                print(f"\n--- Aktualizacja dla Kategorii: {category.name} ---")
                update_discipline_positions(category)
                # Następnie aktualizujemy wyniki ogólne DLA CAŁEJ KATEGORII
                update_overall_results_for_category(category)
        print(f"=== Zakończono pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    except Exception as e:
         print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id}: {e}")
         traceback.print_exc()

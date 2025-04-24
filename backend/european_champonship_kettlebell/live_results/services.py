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

def update_discipline_positions(category: Category) -> None:
    """
    Calculates and updates positions for players within a category
    for each relevant discipline. Includes detailed debugging prints.
    """
    print(f"\n=== DEBUG: Rozpoczynam update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===") # DEBUG START Function

    players_in_category = Player.objects.filter(categories=category).only("id", "weight", "surname", "name")
    if not players_in_category.exists():
        print(f"DEBUG: Brak graczy w kategorii {category.id} ('{category.name}'). Pomijam obliczanie pozycji dyscyplin.")
        print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (Brak graczy) ===") # DEBUG END Function (No players)
        return

    player_ids = list(players_in_category.values_list("id", flat=True))
    print(f"DEBUG: Znaleziono graczy w kategorii (IDs): {player_ids}")

    disciplines = category.get_disciplines()
    if not disciplines:
        print(f"DEBUG: Kategoria {category.id} ('{category.name}') nie ma zdefiniowanych dyscyplin. Pomijam obliczanie pozycji.")
        print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (Brak dyscyplin) ===") # DEBUG END Function (No disciplines)
        return

    # Słownik mapujący stałą dyscypliny na pole, wg którego sortujemy (malejąco)
    ordering_logic = {
        SNATCH: "-calculated_snatch_score",
        TGU: "-tgu_bw_ratio",
        ONE_KB_PRESS: "-okbp_bw_ratio",
        KB_SQUAT: "-kbs_bw_ratio",
        TWO_KB_PRESS: "-tkbp_bw_ratio",
    }

    print(f"DEBUG: Dyscypliny do przetworzenia w kategorii: {disciplines}")
    for discipline in disciplines:
        print(f"\n  --- DEBUG: Przetwarzanie dyscypliny: {discipline} ---") # DEBUG START Discipline

        if discipline not in DISCIPLINE_MODELS_MAP:
            print(f"  DEBUG WARNING: Pomijam nieznaną dyscyplinę '{discipline}' w kategorii {category.id}")
            continue

        model = DISCIPLINE_MODELS_MAP[discipline]
        order_by_field = ordering_logic.get(discipline)
        if not order_by_field:
            print(f"  DEBUG WARNING: Brak logiki sortowania dla dyscypliny '{discipline}'. Pomijam.")
            continue

        print(f"  DEBUG: Model={model.__name__}, Sortowanie po={order_by_field}")
        results_qs = model.objects.select_related("player").filter(player_id__in=player_ids)

        # Adnotacje do obliczenia wyniku sortującego
        annotated_qs = results_qs # Domyślnie, jeśli nie ma specjalnej logiki
        annotation_field_name = None # Nazwa pola z wynikiem do rankingu

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
                print(f"  DEBUG: Dodano adnotację '{annotation_field_name}' dla {discipline}")
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
                print(f"  DEBUG: Dodano adnotacje 'max_tgu_result', '{annotation_field_name}' dla {discipline}")
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
                print(f"  DEBUG: Dodano adnotacje 'max_okbp_result', '{annotation_field_name}' dla {discipline}")
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
                print(f"  DEBUG: Dodano adnotacje 'max_kbs_result', '{annotation_field_name}' dla {discipline}")
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
                print(f"  DEBUG: Dodano adnotacje 'max_tkbp_result', '{annotation_field_name}' dla {discipline}")
            else:
                 print(f"  DEBUG WARNING: Brak specyficznej adnotacji dla {discipline}. Sortowanie może nie działać poprawnie.")

            if not annotation_field_name:
                 print(f"  DEBUG ERROR: Nie udało się ustalić pola adnotacji dla {discipline}. Pomijam ranking.")
                 continue

            # Sortowanie
            ordered_results = annotated_qs.order_by(order_by_field, "player__surname", "player__name")
            print(f"  DEBUG: Wyniki posortowane. Liczba wyników: {ordered_results.count()}")

            # Fragment funkcji update_discipline_positions w services.py

            # ... (kod przed pętlą for result in ordered_results:) ...
            updates = []
            current_pos = 0
            last_score = None
            rank_counter = 0
            tie_start_rank = 1

            # Usuwamy epsilon z nagłówka logu, bo go nie użyjemy
            print(f"    --- DEBUG: Rozpoczynam pętlę rankingu dla {discipline} ---")
            for result in ordered_results:
                rank_counter += 1
                player_str = f"{result.player.surname} {result.player.name}" if result.player else f"Gracz ID:{result.player_id}"
                score = 0.0

                try:
                    score = getattr(result, annotation_field_name, 0.0)
                    score = float(score or 0.0)
                except (AttributeError, TypeError, ValueError) as e_score:
                    score = 0.0
                    print(
                        f"      DEBUG WARNING: Błąd pobierania score ({annotation_field_name}) dla {player_str}: {e_score}")

                print(f"\n    [Iteracja {rank_counter}]")
                print(f"      Zawodnik: {player_str} (Wynik ID: {result.id})")
                print(f"      Aktualny obliczony Score (do rankingu): {score:.10f}")  # Nadal wyświetlamy z precyzją
                print(
                    f"      Poprzedni Score (last_score): {last_score if last_score is not None else 'Brak (pierwszy element)'}{'.' if last_score is None else f':.10f'}")

                # --- ZMIANA LOGIKI REMISU ---
                # Używamy bezpośredniego porównania ZAMIAST epsilon
                # UWAGA: Ryzykowne dla liczb float! Działa tylko jeśli masz pewność,
                # że wyniki remisujących SĄ DOKŁADNIE IDENTYCZNE bitowo.
                is_tie = False
                if last_score is not None:
                    # BEZPOŚREDNIE PORÓWNANIE
                    if score == last_score:
                        is_tie = True
                # -----------------------------

                print(
                    f"      Czy jest remis z poprzednim? {'TAK' if is_tie else 'NIE'} (warunek: {score:.10f} == {f'{last_score:.10f}' if last_score is not None else 'None'} -> {score == last_score if last_score is not None else 'N/A'})")

                if not is_tie:
                    current_pos = rank_counter
                    last_score = score
                    tie_start_rank = rank_counter
                    print(
                        f"      -> Nie ma remisu (lub pierwszy). Nowa pozycja = rank_counter = {current_pos}. Nowy last_score = {last_score:.10f}. Nowy tie_start_rank = {tie_start_rank}.")
                else:
                    current_pos = tie_start_rank
                    print(f"      -> Jest remis. Pozycja = tie_start_rank = {current_pos}.")

                db_position = result.position
                print(f"      Pozycja z Bazy Danych (result.position): {db_position}")
                print(f"      Pozycja Obliczona (current_pos): {current_pos}")

                needs_update = False
                if db_position != current_pos or db_position is None:
                    needs_update = True
                    result.position = current_pos
                    updates.append(result)

                print(f"      Czy wymaga aktualizacji w DB? {'TAK' if needs_update else 'NIE'}")

            print(f"    --- DEBUG: Zakończono pętlę rankingu. Liczba potencjalnych aktualizacji: {len(updates)} ---")

            # ... (reszta kodu funkcji update_discipline_positions i całego pliku) ...

            if updates:
                try:
                    # Użyj transakcji dla pewności, chociaż cała funkcja update_overall_results_for_player powinna być atomowa
                    with transaction.atomic():
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

        print(f"  --- DEBUG: Zakończono przetwarzanie dyscypliny: {discipline} ---") # DEBUG END Discipline

    print(f"=== DEBUG: Kończę update_discipline_positions dla kategorii: {category.name} (ID: {category.id}) ===") # DEBUG END Function


def update_overall_results_for_category(category: Category) -> None:
    """Calculates and updates overall points and final positions for players within a category."""
    # Updated prefetch_related
    players_in_category = Player.objects.filter(categories=category).prefetch_related(
        "snatch_result",
        "tgu_result",
        # "pistol_squat_result", # Commented out
        # "see_saw_press_result", # Commented out
        "kb_squat_one_result", # Updated related name
        "one_kettlebell_press_result",
        "two_kettlebell_press_one_result", # Updated related name
        "overallresult",
    )
    if not players_in_category.exists():
        print(f"Brak graczy w kategorii {category.id}. Pomijam obliczanie wyników ogólnych.")
        return

    print(f"Aktualizacja wyników ogólnych dla kategorii: {category.name} ({category.id})")
    disciplines_in_category = category.get_disciplines()
    overall_updates = []
    final_pos_updates = []

    # Updated discipline_related_names
    discipline_related_names = {
        SNATCH: "snatch_result",
        TGU: "tgu_result",
        # PISTOL_SQUAT: "pistol_squat_result", # Commented out
        # SEE_SAW_PRESS: "see_saw_press_result", # Commented out
        KB_SQUAT: "kb_squat_one_result", # Updated related name
        ONE_KB_PRESS: "one_kettlebell_press_result",
        TWO_KB_PRESS: "two_kettlebell_press_one_result", # Updated related name
    }
    # Updated overall_points_fields
    overall_points_fields = {
        SNATCH: "snatch_points",
        TGU: "tgu_points",
        # PISTOL_SQUAT: "pistol_squat_points", # Commented out
        # SEE_SAW_PRESS: "see_saw_press_points", # Commented out
        KB_SQUAT: "kb_squat_points",
        ONE_KB_PRESS: "one_kb_press_points",
        TWO_KB_PRESS: "two_kb_press_points",
    }

    for player in players_in_category:
        overall_result, created_overall = OverallResult.objects.get_or_create(player=player)
        if created_overall:
            print(f"  Stworzono brakujący rekord OverallResult dla gracza {player.id}")

        changed = False
        # Clear points fields before recalculating
        for field_name in overall_points_fields.values():
            if getattr(overall_result, field_name, None) is not None:
                setattr(overall_result, field_name, None) # Set to None initially
                changed = True

        new_tiebreak_points = -0.5 if player.tiebreak else 0.0
        if overall_result.tiebreak_points != new_tiebreak_points:
            overall_result.tiebreak_points = new_tiebreak_points
            changed = True

        # Recalculate points based on current discipline positions
        for disc_const, related_name in discipline_related_names.items():
            points_field = overall_points_fields.get(disc_const)
            if not points_field: continue # Skip if discipline is not in overall points (e.g. commented out)

            if disc_const in disciplines_in_category:
                result_obj = getattr(player, related_name, None)
                new_points = None
                if result_obj and hasattr(result_obj, "position") and result_obj.position is not None:
                    new_points = float(result_obj.position)

                if getattr(overall_result, points_field, None) != new_points:
                    setattr(overall_result, points_field, new_points)
                    changed = True
            else:
                # If discipline is NOT in the category, ensure points are None
                if getattr(overall_result, points_field, None) is not None:
                    setattr(overall_result, points_field, None)
                    changed = True

        old_total_points = overall_result.total_points
        overall_result.calculate_total_points()
        if old_total_points != overall_result.total_points:
            changed = True

        if changed or created_overall:
            overall_updates.append(overall_result)

    if overall_updates:
        update_fields = list(overall_points_fields.values()) + ["tiebreak_points", "total_points"]
        try:
            updated_points_count = OverallResult.objects.bulk_update(overall_updates, update_fields)
            print(f"  Zaktualizowano punkty OverallResult dla {updated_points_count} graczy.")
        except Exception as e_bulk_overall:
            print(f"  BŁĄD bulk_update punktów OverallResult w kategorii {category.id}: {e_bulk_overall}")
            traceback.print_exc()

    # Calculate Final Positions
    final_results = OverallResult.objects.filter(player__categories=category).order_by(
        "total_points", "player__surname", "player__name"
    )

    current_final_pos = 0
    last_total_points = None
    final_rank_counter = 0

    for result in final_results:
        final_rank_counter += 1
        current_total_points = result.total_points

        should_update_pos = False
        if last_total_points is None:
            should_update_pos = True
        elif current_total_points is None and last_total_points is not None:
            should_update_pos = True
        elif current_total_points is not None and last_total_points is None:
            should_update_pos = True
        elif (
            current_total_points is not None
            and last_total_points is not None
            and abs(current_total_points - last_total_points) > epsilon
        ):
            should_update_pos = True

        if should_update_pos:
            current_final_pos = final_rank_counter
        last_total_points = current_total_points

        if result.final_position != current_final_pos:
            result.final_position = current_final_pos
            final_pos_updates.append(result)

    if final_pos_updates:
        try:
            updated_pos_count = OverallResult.objects.bulk_update(final_pos_updates, ["final_position"])
            print(f"  Zaktualizowano final_position OverallResult dla {updated_pos_count} graczy.")
        except Exception as e_bulk_final:
            print(f"  BŁĄD bulk_update final_position OverallResult w kategorii {category.id}: {e_bulk_final}")
            traceback.print_exc()
    else:
        print("  Brak zmian final_position OverallResult do zapisania.")


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


def update_overall_results_for_player(player: Player) -> None:
    """
    Updates discipline positions and overall results for ALL categories
    a player belongs to. Wrapped in a transaction.
    """
    if not hasattr(player, "categories"):
        print(f"Obiekt gracza {player.id} nie ma atrybutu 'categories'. Pomijam aktualizację.")
        return
    if not player.categories.exists():
        print(f"Gracz {player.id} nie ma przypisanych kategorii. Pomijam aktualizację overall.")
        return

    print(f"=== Rozpoczynam pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    try:
        with transaction.atomic():
            categories = list(player.categories.all())
            if not categories:
                print(f"Gracz {player.id} nie ma kategorii po pobraniu listy. Kończę.")
                return

            print(f"Aktualizuję wyniki dla gracza {player.id} w kategoriach: {[c.name for c in categories]}")
            for category in categories:
                print(f"\n--- Aktualizacja dla Kategorii: {category.name} ---")
                update_discipline_positions(category) # Uses updated logic
                update_overall_results_for_category(category) # Uses updated logic
        print(f"=== Zakończono pełną aktualizację wyników dla gracza: {player} ({player.id}) ===")
    except Exception as e:
        print(f"!!! KRYTYCZNY BŁĄD podczas pełnej aktualizacji dla gracza {player.id}: {e}")
        traceback.print_exc()

import traceback

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Player
# Updated results import
from .models.results import (
    KBSquatResult, OneKettlebellPressResult, # PistolSquatResult removed
    # SeeSawPressResult removed
    SnatchResult, TGUResult, TwoKettlebellPressResult,
)
from .services import (
    create_default_results_for_player_categories,
    update_overall_results_for_player,
)

# Updated RESULT_MODELS_TO_TRACK
RESULT_MODELS_TO_TRACK = [
    SnatchResult, TGUResult, # SeeSawPressResult removed
    KBSquatResult,
    # PistolSquatResult removed
    OneKettlebellPressResult, TwoKettlebellPressResult,
]


@receiver(post_save, sender=RESULT_MODELS_TO_TRACK)
def trigger_overall_update_on_result_save(sender, instance, created, **kwargs):
    """
    Triggers overall results update for the player when a tracked
    individual Result model instance is saved.
    """
    player_instance = getattr(instance, "player", None)
    if player_instance and isinstance(player_instance, Player):
        print(
            f"[Signal post_save] Zapisano {sender.__name__} dla gracza {player_instance.id}. Uruchamiam aktualizację wyników..."
        )
        try:
            # Calls the updated service function
            update_overall_results_for_player(player_instance)
        except Exception as e:
            print(
                f"[Signal post_save] KRYTYCZNY BŁĄD podczas aktualizacji dla {sender.__name__} (Gracz: {player_instance.id}): {e}"
            )
            traceback.print_exc()


@receiver(m2m_changed, sender=Player.categories.through)
def handle_player_category_change(sender, instance, action, pk_set, **kwargs):
    """
    Handles changes to the Player-Category relationship (Player.categories).
    - When a player is ADDED to categories ('post_add'):
        1. Creates default (zeroed) result entries for ALL current categories.
        2. Triggers a full results update for the player.
    - Logic is wrapped in transaction.on_commit for safety.
    """
    print(
        f"[Signal m2m_changed TRIGGERED] Instance: {instance} (Type: {type(instance)}), Action: {action}, PKs: {pk_set}"
    )
    if not isinstance(instance, Player):
        print(
            f"[Signal m2m_changed] Ostrzeżenie: Otrzymano sygnał dla instancji typu {type(instance)}, oczekiwano Player."
        )
        return

    player = instance

    if action == "post_add" and pk_set:
        print(
            f"[Signal m2m_changed] Gracz {player.id} dodany do kategorii PKs: {pk_set}. Planuję przetwarzanie po zatwierdzeniu transakcji..."
        )

        def process_after_commit():
            print(
                f"[Signal m2m_changed on_commit] Rozpoczynam przetwarzanie dla Gracza {player.id}..."
            )
            try:
                # Ensure player still exists and refresh categories
                player.refresh_from_db()
                all_category_pks = set(player.categories.all().values_list('pk', flat=True))
                print(
                    f"[Signal m2m_changed on_commit] Gracz {player.id}: Aktualne kategorie PKs po odświeżeniu: {all_category_pks}"
                )

                if not all_category_pks:
                    print(
                        f"[Signal m2m_changed on_commit WARNING] Gracz {player.id}: Brak kategorii po odświeżeniu! Pomijam dalsze kroki."
                    )
                    return

                print(
                    f"[Signal m2m_changed on_commit] Gracz {player.id}: Tworzenie/sprawdzanie domyślnych wyników dla kategorii {all_category_pks}..."
                )
                # Calls the updated service function
                created_defaults = create_default_results_for_player_categories(player, all_category_pks)
                if created_defaults:
                    print(
                        f"[Signal m2m_changed on_commit] Stworzono nowe domyślne rekordy wyników dla gracza {player.id}.")
                else:
                    print(
                        f"[Signal m2m_changed on_commit] Nie stworzono nowych domyślnych rekordów (prawdopodobnie już istniały) dla gracza {player.id}."
                    )

                print(
                    f"[Signal m2m_changed on_commit] Uruchamiam pełną aktualizację wyników dla gracza {player.id}..."
                )
                # Calls the updated service function
                update_overall_results_for_player(player)
                print(
                    f"[Signal m2m_changed on_commit] Zakończono przetwarzanie dla gracza {player.id}."
                )

            except Player.DoesNotExist:
                print(f"[Signal m2m_changed on_commit ERROR] Player {player.id} nie istnieje już w bazie?")
            except Exception as e:
                print(
                    f"[Signal m2m_changed on_commit] KRYTYCZNY BŁĄD podczas obsługi dodania gracza {player.id} do kategorii: {e}"
                )
                traceback.print_exc()

        transaction.on_commit(process_after_commit)

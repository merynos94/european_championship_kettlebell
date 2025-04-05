import traceback

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Player
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    PistolSquatResult,
    SeeSawPressResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)
from .services import (
    create_default_results_for_player_categories,
    update_overall_results_for_player,
)

RESULT_MODELS_TO_TRACK = [
    SnatchResult,
    TGUResult,
    SeeSawPressResult,
    KBSquatResult,
    PistolSquatResult,
    OneKettlebellPressResult,
    TwoKettlebellPressResult,
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
        1. Creates default (zeroed) result entries for relevant disciplines.
        2. Triggers a full results update for the player.
    """
    if not isinstance(instance, Player):
        print(
            f"[Signal m2m_changed] Ostrzeżenie: Otrzymano sygnał dla instancji typu {type(instance)}, oczekiwano Player."
        )
        return

    player = instance
    if action == "post_add" and pk_set:
        print(f"[Signal m2m_changed] Gracz {player.id} dodany do kategorii PKs: {pk_set}. Rozpoczynam przetwarzanie...")
        try:
            created_defaults = create_default_results_for_player_categories(player, pk_set)
            if created_defaults:
                print(f"[Signal m2m_changed] Stworzono domyślne rekordy wyników dla gracza {player.id}.")
            else:
                print(
                    f"[Signal m2m_changed] Nie stworzono nowych domyślnych rekordów (prawdopodobnie już istniały) dla gracza {player.id}."
                )
            print(
                f"[Signal m2m_changed] Uruchamiam pełną aktualizację wyników dla gracza {player.id} po zmianie kategorii..."
            )
            update_overall_results_for_player(player)
            print(f"[Signal m2m_changed] Zakończono przetwarzanie dla gracza {player.id}.")

        except Exception as e:
            print(f"[Signal m2m_changed] KRYTYCZNY BŁĄD podczas obsługi dodania gracza {player.id} do kategorii: {e}")
            traceback.print_exc()

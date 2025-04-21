import traceback

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Player
from .models.results import (
    KBSquatResult,
    OneKettlebellPressResult,
    SnatchResult,
    TGUResult,
    TwoKettlebellPressResult,
)
from .services import (
    create_default_results_for_player_categories,
    update_overall_results_for_player,
)
RESULT_MODELS_TO_TRACK = [
    SnatchResult, TGUResult, KBSquatResult,
    OneKettlebellPressResult, TwoKettlebellPressResult,
]

def handle_result_save_logic(sender, instance, created, **kwargs):
    """
    Shared logic to handle result save.
    Schedules the actual update to run after the transaction commits.
    """
    player_instance = getattr(instance, "player", None)
    if player_instance and isinstance(player_instance, Player):
        player_id = player_instance.id
        print(
            f"[Signal post_save - {sender.__name__}] Zapisano dla gracza {player_id}. "
            f"Planuję aktualizację wyników po zatwierdzeniu transakcji..."
        )

        # Funkcja, która zostanie wykonana PO zatwierdzeniu transakcji
        def process_update_after_commit():
            print(f"[Signal post_save on_commit - {sender.__name__}] Rozpoczynam aktualizację dla gracza {player_id}...")
            try:
                player_to_update = Player.objects.get(pk=player_id)
                update_overall_results_for_player(player_to_update)
                print(f"[Signal post_save on_commit - {sender.__name__}] Zakończono aktualizację dla gracza {player_id}.")
            except Player.DoesNotExist:
                 print(f"[Signal post_save on_commit ERROR - {sender.__name__}] Gracz {player_id} nie istnieje już w bazie?")
            except Exception as e:
                print(
                    f"[Signal post_save on_commit ERROR - {sender.__name__}] KRYTYCZNY BŁĄD podczas aktualizacji dla gracza {player_id}: {e}"
                )
                traceback.print_exc()

        transaction.on_commit(process_update_after_commit)


@receiver(post_save, sender=SnatchResult)
def trigger_snatch_update(sender, instance, created, **kwargs):
    """Receiver for SnatchResult post_save signal."""
    handle_result_save_logic(sender, instance, created, **kwargs)

@receiver(post_save, sender=TGUResult)
def trigger_tgu_update(sender, instance, created, **kwargs):
    """Receiver for TGUResult post_save signal."""
    handle_result_save_logic(sender, instance, created, **kwargs)

@receiver(post_save, sender=KBSquatResult)
def trigger_kbsquat_update(sender, instance, created, **kwargs):
    """Receiver for KBSquatResult post_save signal."""
    handle_result_save_logic(sender, instance, created, **kwargs)

@receiver(post_save, sender=OneKettlebellPressResult)
def trigger_okbp_update(sender, instance, created, **kwargs):
    """Receiver for OneKettlebellPressResult post_save signal."""
    handle_result_save_logic(sender, instance, created, **kwargs)

@receiver(post_save, sender=TwoKettlebellPressResult)
def trigger_tkbp_update(sender, instance, created, **kwargs):
    """Receiver for TwoKettlebellPressResult post_save signal."""
    handle_result_save_logic(sender, instance, created, **kwargs)

@receiver(m2m_changed, sender=Player.categories.through)
def handle_player_category_change(sender, instance, action, pk_set, **kwargs):
    """
    Handles changes to the Player-Category relationship (Player.categories).
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

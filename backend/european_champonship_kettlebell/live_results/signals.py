import traceback
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.results import (
    KBSquatResult, OneKettlebellPressResult, PistolSquatResult,
    SeeSawPressResult, SnatchResult, TGUResult, TwoKettlebellPressResult
)
from .services import update_overall_results_for_player

RESULT_MODELS_TO_TRACK = [
    SnatchResult, TGUResult, SeeSawPressResult, KBSquatResult,
    PistolSquatResult, OneKettlebellPressResult, TwoKettlebellPressResult
]

@receiver(post_save, sender=RESULT_MODELS_TO_TRACK)
def trigger_overall_update_on_result_save(sender, instance, created, **kwargs):
    """Triggers overall results update when a tracked Result model is saved."""
    if hasattr(instance, 'player') and instance.player:
        print(f"Sygnał post_save od {sender.__name__} dla gracza {instance.player.id}. Aktualizacja...")
        try:
            update_overall_results_for_player(instance.player)
        except Exception as e:
            print(f"KRYTYCZNY BŁĄD w sygnale post_save dla {sender.__name__} (Gracz: {instance.player.id}): {e}")
            traceback.print_exc()
    else:
         print(f"Sygnał post_save od {sender.__name__} bez gracza (ID instancji: {instance.pk}). Ignoruję.")

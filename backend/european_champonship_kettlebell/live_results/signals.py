# live_results/signals.py

import traceback
from django.db.models.signals import post_save, m2m_changed # Dodano m2m_changed
from django.dispatch import receiver

# --- Importy Modeli ---
# Zakładamy, że modele są w podkatalogu 'models' aplikacji 'live_results'
from .models import Player # Wystarczy Player do sprawdzania typu instancji

# Importuj modele wyników do śledzenia przez post_save
from .models.results import (
    KBSquatResult, OneKettlebellPressResult, PistolSquatResult,
    SeeSawPressResult, SnatchResult, TGUResult, TwoKettlebellPressResult
)

# --- Importy Usług ---
from .services import (
    update_overall_results_for_player,
    create_default_results_for_player_categories # Import nowej funkcji
)

# Lista modeli wyników, których zapis wywołuje aktualizację ogólną
RESULT_MODELS_TO_TRACK = [
    SnatchResult, TGUResult, SeeSawPressResult, KBSquatResult,
    PistolSquatResult, OneKettlebellPressResult, TwoKettlebellPressResult
]
# signals.py
# ... (reszta kodu bez zmian) ...

# --- Sygnał po Zapisie Wyniku Indywidualnego ---
@receiver(post_save, sender=RESULT_MODELS_TO_TRACK)
def trigger_overall_update_on_result_save(sender, instance, created, **kwargs):
    """
    Triggers overall results update for the player when a tracked
    individual Result model instance is saved.
    """
    player_instance = getattr(instance, 'player', None)
    # Sprawdzamy, czy mamy instancję gracza i czy jest ona poprawnym obiektem Player
    if player_instance and isinstance(player_instance, Player):
        print(f"[Signal post_save] Zapisano {sender.__name__} dla gracza {player_instance.id}. Uruchamiam aktualizację wyników...")
        try:
            # Wywołujemy pełną aktualizację dla tego gracza
            # Ta funkcja zajmie się wszystkimi jego kategoriami
            update_overall_results_for_player(player_instance)
        except Exception as e:
            print(f"[Signal post_save] KRYTYCZNY BŁĄD podczas aktualizacji dla {sender.__name__} (Gracz: {player_instance.id}): {e}")
            traceback.print_exc()
    # else:
         # Zakomentowany blok else - nie robimy nic, jeśli nie ma poprawnego gracza
         # print(f"[Signal post_save] Sygnał od {sender.__name__} bez poprawnego gracza (ID instancji: {instance.pk}). Ignoruję.")
    # pass <--- USUNIĘTO TĘ LINIĘ

# --- Sygnał po Zmianie Kategorii Gracza ---
# ... (reszta kodu bez zmian) ...


# --- Sygnał po Zmianie Kategorii Gracza ---
@receiver(m2m_changed, sender=Player.categories.through)
def handle_player_category_change(sender, instance, action, pk_set, **kwargs):
    """
    Handles changes to the Player-Category relationship (Player.categories).
    - When a player is ADDED to categories ('post_add'):
        1. Creates default (zeroed) result entries for relevant disciplines.
        2. Triggers a full results update for the player.
    """
    # 'instance' w tym sygnale to obiekt Player, którego dotyczy zmiana M2M
    if not isinstance(instance, Player):
        # Dodatkowe zabezpieczenie, chociaż sender=Player.categories.through powinien to gwarantować
        print(f"[Signal m2m_changed] Ostrzeżenie: Otrzymano sygnał dla instancji typu {type(instance)}, oczekiwano Player.")
        return

    player = instance

    # Interesuje nas tylko akcja 'post_add' (po dodaniu do kategorii)
    # i tylko jeśli faktycznie dodano jakieś kategorie (pk_set nie jest pusty)
    if action == "post_add" and pk_set:
        print(f"[Signal m2m_changed] Gracz {player.id} dodany do kategorii PKs: {pk_set}. Rozpoczynam przetwarzanie...")
        try:
            # Krok 1: Stwórz domyślne (zerowe) rekordy wyników dla nowych kategorii
            # Funkcja zwraca True, jeśli cokolwiek zostało stworzone
            created_defaults = create_default_results_for_player_categories(player, pk_set)
            if created_defaults:
                 print(f"[Signal m2m_changed] Stworzono domyślne rekordy wyników dla gracza {player.id}.")
            else:
                 print(f"[Signal m2m_changed] Nie stworzono nowych domyślnych rekordów (prawdopodobnie już istniały) dla gracza {player.id}.")

            # Krok 2: ZAWSZE uruchom pełną aktualizację wyników dla gracza po dodaniu go do kategorii.
            # Jest to konieczne, ponieważ nawet jeśli rekordy już istniały,
            # samo dodanie gracza do nowej kategorii wpływa na ranking w tej kategorii.
            print(f"[Signal m2m_changed] Uruchamiam pełną aktualizację wyników dla gracza {player.id} po zmianie kategorii...")
            update_overall_results_for_player(player)
            print(f"[Signal m2m_changed] Zakończono przetwarzanie dla gracza {player.id}.")

        except Exception as e:
            print(f"[Signal m2m_changed] KRYTYCZNY BŁĄD podczas obsługi dodania gracza {player.id} do kategorii: {e}")
            traceback.print_exc()

    # Można dodać obsługę innych akcji, np. 'post_remove', jeśli usunięcie
    # z kategorii również powinno wywołać przeliczenie wyników.
    # elif action == "post_remove" and pk_set:
    #     print(f"[Signal m2m_changed] Gracz {player.id} usunięty z kategorii PKs: {pk_set}. Uruchamiam aktualizację wyników...")
    #     try:
    #         # Po usunięciu z kategorii, również przeliczamy wyniki
    #         # Nie musimy usuwać rekordów wyników, ale rankingi się zmienią
    #         update_overall_results_for_player(player)
    #         # Dodatkowo trzeba przeliczyć wyniki w kategoriach, z których gracz został usunięty
    #         # To wymaga pobrania tych kategorii i wywołania dla nich aktualizacji
    #         removed_categories = Category.objects.filter(pk__in=pk_set)
    #         for category in removed_categories:
    #              print(f"[Signal m2m_changed] Aktualizacja kategorii {category.name} po usunięciu gracza {player.id}...")
    #              update_discipline_positions(category)
    #              update_overall_results_for_category(category)
    #     except Exception as e:
    #         print(f"[Signal m2m_changed] KRYTYCZNY BŁĄD podczas obsługi usunięcia gracza {player.id} z kategorii: {e}")
    #         traceback.print_exc()

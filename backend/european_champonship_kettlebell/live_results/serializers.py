# Plik: serializers.py

from rest_framework import serializers

# Importuj NOWY model CategoryOverallResult
from .models.results.overall import CategoryOverallResult
# Importuj pozostałe modele i serializery jak wcześniej
from .models.category import Category
from .models.sport_club import SportClub
from .models.player import Player
from .models.results import (
    SnatchResult, TGUResult, KBSquatResult, # Upewnij się, że te modele są zaktualizowane!
    OneKettlebellPressResult, TwoKettlebellPressResult,
)

# --- Podstawowe Serializery (bez zmian) ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = ['id', 'name', 'disciplines']

class SportClubSerializer(serializers.ModelSerializer):
    class Meta: model = SportClub; fields = ['id', 'name']

class PlayerBasicInfoSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True, allow_null=True)
    class Meta: model = Player; fields = ['id', 'name', 'surname', 'club_name', 'weight']; read_only_fields = fields

# --- Serializery Wyników Dyscyplin (bez zmian) ---
# Upewnij się, że używają poprawnych pól (result_1/2/3, max_result_val, bw_percentage_val)
class SnatchResultSerializer(serializers.ModelSerializer):
    result_score = serializers.SerializerMethodField()
    class Meta: model = SnatchResult; fields = ['kettlebell_weight', 'repetitions', 'result_score']; # Usunięto 'position' jeśli niepotrzebne
    def get_result_score(self, obj: SnatchResult) -> float:
        score = obj.result # Używa @property z modelu
        return score if score is not None else 0.0

class TGUResultSerializer(serializers.ModelSerializer):
    # max_result_val i bw_percentage_val mogą być teraz polami modelu
    class Meta: model = TGUResult; fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']; # Usunięto 'position'

class OneKettlebellPressResultSerializer(serializers.ModelSerializer):
    class Meta: model = OneKettlebellPressResult; fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']; # Usunięto 'position'

class KBSquatResultSerializer(serializers.ModelSerializer):
    class Meta: model = KBSquatResult; fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']; # Usunięto 'position'

class TwoKettlebellPressResultSerializer(serializers.ModelSerializer):
    class Meta: model = TwoKettlebellPressResult; fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']; # Usunięto 'position'


# --- ZMODYFIKOWANY Główny Serializer Wyników ---
class CategoryResultsSerializer(serializers.ModelSerializer):
    """Serializuje wyniki CategoryOverallResult dla danej kategorii."""
    player = PlayerBasicInfoSerializer(read_only=True) # Pobiera dane z powiązanego gracza

    # Zagnieżdżone wyniki - źródło nadal wskazuje na relacje w modelu Player
    # Widok musi zapewnić, że te relacje są dostępne (przez select/prefetch_related)
    snatch_result = SnatchResultSerializer(source='player.snatch_result', read_only=True, allow_null=True)
    tgu_result = TGUResultSerializer(source='player.tgu_result', read_only=True, allow_null=True)
    kb_squat_result = KBSquatResultSerializer(source='player.kb_squat_one_result', read_only=True, allow_null=True) # Sprawdź related_name!
    one_kettlebell_press_result = OneKettlebellPressResultSerializer(source='player.one_kettlebell_press_result', read_only=True, allow_null=True)
    two_kettlebell_press_result = TwoKettlebellPressResultSerializer(source='player.two_kettlebell_press_one_result', read_only=True, allow_null=True) # Sprawdź related_name!

    class Meta:
        model = CategoryOverallResult # ZMIANA MODELU!
        fields = [
            'final_position', # Bezpośrednio z CategoryOverallResult
            'player',         # Zagnieżdżony Player
            'total_points',   # Bezpośrednio z CategoryOverallResult
            'snatch_points',  # Bezpośrednio z CategoryOverallResult
            'tgu_points',     # ...
            'kb_squat_points',
            'one_kb_press_points',
            'two_kb_press_points',
            'tiebreak_points',
            # Zagnieżdżone wyniki dyscyplin
            'snatch_result',
            'tgu_result',
            'kb_squat_result',
            'one_kettlebell_press_result',
            'two_kettlebell_press_result',
        ]
        # Wszystkie pola są tylko do odczytu w tym kontekście
        read_only_fields = fields
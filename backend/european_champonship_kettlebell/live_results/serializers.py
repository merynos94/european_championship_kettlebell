# Plik: serializers.py

from rest_framework import serializers

# Importuj NOWY model CategoryOverallResult
from .models.results.overall import CategoryOverallResult
# Importuj pozostałe modele
from .models.category import Category
from .models.sport_club import SportClub
from .models.player import Player
from .models.results import (
    SnatchResult, TGUResult, KBSquatResult,
    OneKettlebellPressResult, TwoKettlebellPressResult,
)

# --- Podstawowe Serializery ---
class CategorySerializer(serializers.ModelSerializer):
    class Meta: model = Category; fields = ['id', 'name', 'disciplines']

class SportClubSerializer(serializers.ModelSerializer):
    class Meta: model = SportClub; fields = ['id', 'name']

class PlayerBasicInfoSerializer(serializers.ModelSerializer):
    club_name = serializers.CharField(source='club.name', read_only=True, allow_null=True)
    class Meta: model = Player; fields = ['id', 'name', 'surname', 'club_name', 'weight']; read_only_fields = fields

# --- Serializery Wyników Dyscyplin - POPRAWIONE ---

class SnatchResultSerializer(serializers.ModelSerializer):
    # Używa SerializerMethodField dla property 'result'
    result_score = serializers.SerializerMethodField()
    class Meta:
        model = SnatchResult
        fields = ['kettlebell_weight', 'repetitions', 'result_score']
        # read_only_fields = ['position'] # Można dodać, jeśli pole istnieje

    def get_result_score(self, obj: SnatchResult) -> float | None:
        # Wywołuje property 'result' z modelu
        # Zmieniono zwracanie None, aby było spójne
        return getattr(obj, 'result', None)

# Wspólna klasa bazowa dla serializera wyników z 3 próbami i property
class BaseSingleAttemptResultSerializer(serializers.ModelSerializer):
    # Używamy SerializerMethodField do pobrania wartości z @property modelu
    max_result_display = serializers.SerializerMethodField()
    bw_percentage_display = serializers.SerializerMethodField()

    class Meta:
        # Model zostanie zdefiniowany w klasach dziedziczących
        fields = [
            'result_1',
            'result_2',
            'result_3',
            'max_result_display',    # Nowa nazwa pola
            'bw_percentage_display', # Nowa nazwa pola
        ]
        # read_only_fields = ['position'] # Jeśli pole istnieje

    def get_max_result_display(self, obj) -> float | None:
        # Wywołuje property 'max_result' - obj będzie instancją TGUResult, KBSquatResult etc.
        val = getattr(obj, 'max_result', None) # Używamy property 'max_result'
        return val # Zwracamy wartość lub None

    def get_bw_percentage_display(self, obj) -> float | None:
        # Wywołuje property 'bw_percentage'
        val = getattr(obj, 'bw_percentage', None) # Używamy property 'bw_percentage'
        return val # Zwracamy wartość lub None

# Serializery dziedziczą teraz z BaseSingleAttemptResultSerializer
class TGUResultSerializer(BaseSingleAttemptResultSerializer):
    class Meta(BaseSingleAttemptResultSerializer.Meta):
        model = TGUResult

class OneKettlebellPressResultSerializer(BaseSingleAttemptResultSerializer):
     class Meta(BaseSingleAttemptResultSerializer.Meta):
        model = OneKettlebellPressResult

class KBSquatResultSerializer(BaseSingleAttemptResultSerializer):
     class Meta(BaseSingleAttemptResultSerializer.Meta):
        model = KBSquatResult

class TwoKettlebellPressResultSerializer(BaseSingleAttemptResultSerializer):
     class Meta(BaseSingleAttemptResultSerializer.Meta):
        model = TwoKettlebellPressResult


# --- Główny Serializer Wyników (bez zmian w stosunku do ostatniej wersji) ---
class CategoryResultsSerializer(serializers.ModelSerializer):
    """Serializuje wyniki CategoryOverallResult dla danej kategorii."""
    player = PlayerBasicInfoSerializer(read_only=True)

    snatch_result = SnatchResultSerializer(source='player.snatch_result', read_only=True, allow_null=True)
    tgu_result = TGUResultSerializer(source='player.tgu_result', read_only=True, allow_null=True)
    kb_squat_result = KBSquatResultSerializer(source='player.kb_squat_one_result', read_only=True, allow_null=True) # Sprawdź related_name!
    one_kettlebell_press_result = OneKettlebellPressResultSerializer(source='player.one_kettlebell_press_result', read_only=True, allow_null=True)
    two_kettlebell_press_result = TwoKettlebellPressResultSerializer(source='player.two_kettlebell_press_one_result', read_only=True, allow_null=True) # Sprawdź related_name!

    class Meta:
        model = CategoryOverallResult # Używa nowego modelu
        fields = [
            'final_position', 'player', 'total_points',
            'snatch_points', 'tgu_points', 'kb_squat_points',
            'one_kb_press_points', 'two_kb_press_points', 'tiebreak_points',
            # Zagnieżdżone wyniki
            'snatch_result', 'tgu_result', 'kb_squat_result',
            'one_kettlebell_press_result', 'two_kettlebell_press_result',
        ]
        read_only_fields = fields
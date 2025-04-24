from rest_framework import serializers

from .models.category import Category
from .models.sport_club import SportClub
from .models.player import Player
from .models.results import (
    OverallResult,
    SnatchResult,
    TGUResult,
    # SeeSawPressResult, # Commented out
    KBSquatResult,
    # PistolSquatResult, # Commented out
    OneKettlebellPressResult,
    TwoKettlebellPressResult,
)


# --- Basic Serializers ---

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model - for listing and basic info."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'disciplines']


class SportClubSerializer(serializers.ModelSerializer):
    """Serializer for the SportClub model - mainly for displaying names."""

    class Meta:
        model = SportClub
        fields = ['id', 'name']


class PlayerBasicInfoSerializer(serializers.ModelSerializer):
    """Minimal serializer for Player - for nesting within results."""
    club_name = serializers.CharField(source='club.name', read_only=True, allow_null=True)

    class Meta:
        model = Player
        fields = ['id', 'name', 'surname', 'club_name', 'weight']
        read_only_fields = fields


# --- Serializers for Individual Discipline Results ---
# These serializers will be nested within the main category results serializer.

class SnatchResultSerializer(serializers.ModelSerializer):
    result_score = serializers.SerializerMethodField()

    class Meta:
        model = SnatchResult
        fields = ['kettlebell_weight', 'repetitions', 'result_score',]
        read_only_fields = ['position']

    def get_result_score(self, obj: SnatchResult) -> float:
        score = obj.result  # Use property 'result' from SnatchResult model
        return score if score is not None else 0.0


class TGUResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = TGUResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']
        read_only_fields = ['position']

    def get_max_result_val(self, obj: TGUResult) -> float:
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: TGUResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class OneKettlebellPressResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = OneKettlebellPressResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val']
        read_only_fields = ['position']

    def get_max_result_val(self, obj: OneKettlebellPressResult) -> float:
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: OneKettlebellPressResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0

# Updated KBSquatResultSerializer for BaseSingleAttemptResult structure
class KBSquatResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = KBSquatResult
        fields = [
            'result_1', 'result_2', 'result_3', # Changed fields
            'max_result_val', 'bw_percentage_val'
        ]
        read_only_fields = ['position']

    def get_max_result_val(self, obj: KBSquatResult) -> float: # Changed method name and logic
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: KBSquatResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


# Updated TwoKettlebellPressResultSerializer for BaseSingleAttemptResult structure
class TwoKettlebellPressResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = TwoKettlebellPressResult
        fields = [
            'result_1', 'result_2', 'result_3', # Changed fields
            'max_result_val', 'bw_percentage_val'
        ]
        read_only_fields = ['position']

    def get_max_result_val(self, obj: TwoKettlebellPressResult) -> float: # Changed method name and logic
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: TwoKettlebellPressResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class CategoryResultsSerializer(serializers.ModelSerializer):
    player = PlayerBasicInfoSerializer(read_only=True)

    snatch_result = SnatchResultSerializer(source='player.snatch_result', read_only=True, allow_null=True)
    tgu_result = TGUResultSerializer(source='player.tgu_result', read_only=True, allow_null=True)
    kb_squat_result = KBSquatResultSerializer(source='player.kb_squat_one_result', read_only=True, allow_null=True) # Updated source
    one_kettlebell_press_result = OneKettlebellPressResultSerializer(source='player.one_kettlebell_press_result',
                                                                     read_only=True, allow_null=True)
    two_kettlebell_press_result = TwoKettlebellPressResultSerializer(source='player.two_kettlebell_press_one_result', # Updated source
                                                                     read_only=True, allow_null=True)

    snatch_points = serializers.SerializerMethodField()
    tgu_points = serializers.SerializerMethodField()
    kb_squat_points = serializers.SerializerMethodField()
    one_kb_press_points = serializers.SerializerMethodField()
    two_kb_press_points = serializers.SerializerMethodField()
    tiebreak_points = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = OverallResult
        # Updated fields list
        fields = [
            'final_position',
            'player',
            'total_points',
            'snatch_points',
            'tgu_points',
            'kb_squat_points',
            'one_kb_press_points',
            'two_kb_press_points',
            'tiebreak_points',
            'snatch_result',
            'tgu_result',
            'kb_squat_result',
            'one_kettlebell_press_result',
            'two_kettlebell_press_result',
        ]
        # Updated read_only_fields list
        read_only_fields = [
            'final_position', 'player', 'snatch_result', 'tgu_result',
            'kb_squat_result',
            'one_kettlebell_press_result', 'two_kettlebell_press_result'
        ]

    def get_snatch_points(self, obj: OverallResult) -> float:
        return obj.snatch_points if obj.snatch_points is not None else 0.0

    def get_tgu_points(self, obj: OverallResult) -> float:
        return obj.tgu_points if obj.tgu_points is not None else 0.0

    def get_kb_squat_points(self, obj: OverallResult) -> float:
        return obj.kb_squat_points if obj.kb_squat_points is not None else 0.0

    def get_one_kb_press_points(self, obj: OverallResult) -> float:
        return obj.one_kb_press_points if obj.one_kb_press_points is not None else 0.0

    def get_two_kb_press_points(self, obj: OverallResult) -> float:
        return obj.two_kb_press_points if obj.two_kb_press_points is not None else 0.0

    def get_tiebreak_points(self, obj: OverallResult) -> float:
        return obj.tiebreak_points if obj.tiebreak_points is not None else 0.0

    def get_total_points(self, obj: OverallResult) -> float:
        return obj.total_points if obj.total_points is not None else 0.0
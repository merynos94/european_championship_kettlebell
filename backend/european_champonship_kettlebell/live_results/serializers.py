from rest_framework import serializers

from .models.category import Category
from .models.sport_club import SportClub
from .models.player import Player
from .models.results import (
    OverallResult,
    SnatchResult,
    TGUResult,
    SeeSawPressResult,
    KBSquatResult,
    PistolSquatResult,
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
        fields = ['kettlebell_weight', 'repetitions', 'result_score', 'position']
        read_only_fields = ['position']

    def get_result_score(self, obj: SnatchResult) -> float:
        score = obj.result  # Użyj property 'result' z modelu SnatchResult
        return score if score is not None else 0.0


class TGUResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = TGUResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
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
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
        read_only_fields = ['position']

    def get_max_result_val(self, obj: OneKettlebellPressResult) -> float:
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: OneKettlebellPressResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class PistolSquatResultSerializer(serializers.ModelSerializer):
    max_result_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = PistolSquatResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
        read_only_fields = ['position']

    def get_max_result_val(self, obj: PistolSquatResult) -> float:
        val = obj.max_result
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: PistolSquatResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class SeeSawPressResultSerializer(serializers.ModelSerializer):
    max_score_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = SeeSawPressResult
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['position']

    def get_max_score_val(self, obj: SeeSawPressResult) -> float:
        val = obj.max_score
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: SeeSawPressResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class KBSquatResultSerializer(serializers.ModelSerializer):
    max_score_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = KBSquatResult
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['position']

    def get_max_score_val(self, obj: KBSquatResult) -> float:
        val = obj.max_score
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: KBSquatResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class TwoKettlebellPressResultSerializer(serializers.ModelSerializer):
    max_score_val = serializers.SerializerMethodField()
    bw_percentage_val = serializers.SerializerMethodField()

    class Meta:
        model = TwoKettlebellPressResult
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['position']

    def get_max_score_val(self, obj: TwoKettlebellPressResult) -> float:
        val = obj.max_score
        return val if val is not None else 0.0

    def get_bw_percentage_val(self, obj: TwoKettlebellPressResult) -> float:
        val = obj.bw_percentage
        return val if val is not None else 0.0


class CategoryResultsSerializer(serializers.ModelSerializer):
    player = PlayerBasicInfoSerializer(read_only=True)

    snatch_result = SnatchResultSerializer(source='player.snatch_result', read_only=True, allow_null=True)
    tgu_result = TGUResultSerializer(source='player.tgu_result', read_only=True, allow_null=True)
    see_saw_press_result = SeeSawPressResultSerializer(source='player.see_saw_press_result', read_only=True,
                                                       allow_null=True)
    kb_squat_result = KBSquatResultSerializer(source='player.kb_squat_result', read_only=True, allow_null=True)
    pistol_squat_result = PistolSquatResultSerializer(source='player.pistol_squat_result', read_only=True,
                                                      allow_null=True)
    one_kettlebell_press_result = OneKettlebellPressResultSerializer(source='player.one_kettlebell_press_result',
                                                                     read_only=True, allow_null=True)
    two_kettlebell_press_result = TwoKettlebellPressResultSerializer(source='player.two_kettlebell_press_result',
                                                                     read_only=True, allow_null=True)

    snatch_points = serializers.SerializerMethodField()
    tgu_points = serializers.SerializerMethodField()
    see_saw_press_points = serializers.SerializerMethodField()
    kb_squat_points = serializers.SerializerMethodField()
    pistol_squat_points = serializers.SerializerMethodField()
    one_kb_press_points = serializers.SerializerMethodField()
    two_kb_press_points = serializers.SerializerMethodField()
    tiebreak_points = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = OverallResult
        fields = [
            'final_position',
            'player',
            'total_points',
            'snatch_points',
            'tgu_points',
            'see_saw_press_points',
            'kb_squat_points',
            'pistol_squat_points',
            'one_kb_press_points',
            'two_kb_press_points',
            'tiebreak_points',
            'snatch_result',
            'tgu_result',
            'see_saw_press_result',
            'kb_squat_result',
            'pistol_squat_result',
            'one_kettlebell_press_result',
            'two_kettlebell_press_result',
        ]
        read_only_fields = [
            'final_position', 'player', 'snatch_result', 'tgu_result',
            'see_saw_press_result', 'kb_squat_result', 'pistol_squat_result',
            'one_kettlebell_press_result', 'two_kettlebell_press_result'
        ]

    def get_snatch_points(self, obj: OverallResult) -> float:
        return obj.snatch_points if obj.snatch_points is not None else 0.0

    def get_tgu_points(self, obj: OverallResult) -> float:
        return obj.tgu_points if obj.tgu_points is not None else 0.0

    def get_see_saw_press_points(self, obj: OverallResult) -> float:
        return obj.see_saw_press_points if obj.see_saw_press_points is not None else 0.0

    def get_kb_squat_points(self, obj: OverallResult) -> float:
        return obj.kb_squat_points if obj.kb_squat_points is not None else 0.0

    def get_pistol_squat_points(self, obj: OverallResult) -> float:
        return obj.pistol_squat_points if obj.pistol_squat_points is not None else 0.0

    def get_one_kb_press_points(self, obj: OverallResult) -> float:
        return obj.one_kb_press_points if obj.one_kb_press_points is not None else 0.0

    def get_two_kb_press_points(self, obj: OverallResult) -> float:
        return obj.two_kb_press_points if obj.two_kb_press_points is not None else 0.0

    def get_tiebreak_points(self, obj: OverallResult) -> float:
        return obj.tiebreak_points if obj.tiebreak_points is not None else 0.0

    def get_total_points(self, obj: OverallResult) -> float:
        return obj.total_points if obj.total_points is not None else 0.0

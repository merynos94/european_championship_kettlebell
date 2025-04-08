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
    # Use source='club.name' to get the club name from the ForeignKey relation
    # read_only=True because we won't set the club name via this serializer
    # allow_null=True in case a player doesn't have an assigned club
    club_name = serializers.CharField(source='club.name', read_only=True, allow_null=True)

    class Meta:
        model = Player
        # Select only the basic fields needed to identify the player in result tables
        fields = ['id', 'name', 'surname', 'club_name', 'weight']
        read_only_fields = fields # All fields read-only in this context

# --- Serializers for Individual Discipline Results ---
# These serializers will be nested within the main category results serializer.

class SnatchResultSerializer(serializers.ModelSerializer):
    """Serializer for Snatch results."""
    # Use source='result' to read the value from the @property in the model
    result_score = serializers.FloatField(source='result', read_only=True)

    class Meta:
        model = SnatchResult
        # Fields relevant for the Snatch results table
        fields = ['kettlebell_weight', 'repetitions', 'result_score', 'position']
        # Position and calculated score are read-only from the API perspective
        read_only_fields = ['result_score', 'position']

class TGUResultSerializer(serializers.ModelSerializer):
    """Serializer for TGU results."""
    # Use source to read values from @property
    max_result_val = serializers.FloatField(source='max_result', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = TGUResult
        # Include attempts and calculated max value & BW percentage
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
        read_only_fields = ['max_result_val', 'bw_percentage_val', 'position']

class OneKettlebellPressResultSerializer(serializers.ModelSerializer):
    """Serializer for One KB Press results."""
    max_result_val = serializers.FloatField(source='max_result', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = OneKettlebellPressResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
        read_only_fields = ['max_result_val', 'bw_percentage_val', 'position']

class PistolSquatResultSerializer(serializers.ModelSerializer):
    """Serializer for Pistol Squat results."""
    max_result_val = serializers.FloatField(source='max_result', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = PistolSquatResult
        fields = ['result_1', 'result_2', 'result_3', 'max_result_val', 'bw_percentage_val', 'position']
        read_only_fields = ['max_result_val', 'bw_percentage_val', 'position']

class SeeSawPressResultSerializer(serializers.ModelSerializer):
    """Serializer for See Saw Press results."""
    max_score_val = serializers.FloatField(source='max_score', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = SeeSawPressResult
        # Include all attempts (left/right) and calculated max value & BW percentage
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['max_score_val', 'bw_percentage_val', 'position']

class KBSquatResultSerializer(serializers.ModelSerializer):
    """Serializer for KB Squat results."""
    max_score_val = serializers.FloatField(source='max_score', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = KBSquatResult
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['max_score_val', 'bw_percentage_val', 'position']

class TwoKettlebellPressResultSerializer(serializers.ModelSerializer):
    """Serializer for Two KB Press results."""
    max_score_val = serializers.FloatField(source='max_score', read_only=True)
    bw_percentage_val = serializers.FloatField(source='bw_percentage', read_only=True)

    class Meta:
        model = TwoKettlebellPressResult
        fields = [
            'result_left_1', 'result_right_1',
            'result_left_2', 'result_right_2',
            'result_left_3', 'result_right_3',
            'max_score_val', 'bw_percentage_val', 'position'
        ]
        read_only_fields = ['max_score_val', 'bw_percentage_val', 'position']

# --- Main Serializer for Category Results ---

class CategoryResultsSerializer(serializers.ModelSerializer):
    """
    Key serializer returning a sorted list of overall results
    for a GIVEN CATEGORY, with nested player data and their
    results in individual disciplines.
    Based on the OverallResult model as it contains the final position and points.
    """
    # Nest basic player info
    player = PlayerBasicInfoSerializer(read_only=True)

    # Nest detailed results from each discipline.
    # Use 'source' to follow relationships: OverallResult -> Player -> SpecificResult
    # allow_null=True is important, as a player might not have a result record for every possible discipline
    snatch_result = SnatchResultSerializer(source='player.snatch_result', read_only=True, allow_null=True)
    tgu_result = TGUResultSerializer(source='player.tgu_result', read_only=True, allow_null=True)
    see_saw_press_result = SeeSawPressResultSerializer(source='player.see_saw_press_result', read_only=True, allow_null=True)
    kb_squat_result = KBSquatResultSerializer(source='player.kb_squat_result', read_only=True, allow_null=True)
    pistol_squat_result = PistolSquatResultSerializer(source='player.pistol_squat_result', read_only=True, allow_null=True)
    one_kettlebell_press_result = OneKettlebellPressResultSerializer(source='player.one_kettlebell_press_result', read_only=True, allow_null=True)
    two_kettlebell_press_result = TwoKettlebellPressResultSerializer(source='player.two_kettlebell_press_result', read_only=True, allow_null=True)

    class Meta:
        model = OverallResult
        # Define the fields to be included in the final JSON
        fields = [
            'final_position',           # Player's final position IN THIS CATEGORY
            'player',                   # Nested player data (name, surname, club, weight)
            'total_points',             # Sum of points (lower is better)

            # Optional: Points from individual disciplines, if needed in the overall summary table
            'snatch_points',
            'tgu_points',
            'see_saw_press_points',
            'kb_squat_points',
            'pistol_squat_points',
            'one_kb_press_points',
            'two_kb_press_points',
            'tiebreak_points',

            # Nested objects with full discipline results - for separate tables on the frontend
            'snatch_result',
            'tgu_result',
            'see_saw_press_result',
            'kb_squat_result',
            'pistol_squat_result',
            'one_kettlebell_press_result',
            'two_kettlebell_press_result',
        ]
        # Since this serializer is for displaying processed category results,
        # all fields should be read-only from this API endpoint's perspective.
        read_only_fields = fields

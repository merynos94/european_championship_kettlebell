"""
Import all models to make them available when importing from the models package.
This allows importing models directly from competitions.models
"""

from .athlete import Athlete
from .athlete_category import AthleteCategory
from .category import Category
from .club import Club
from .exercise import Exercise
from .exercise_type import ExerciseType

# Make all models available at the package level
__all__ = ["Club", "Category", "ExerciseType", "Athlete", "AthleteCategory", "Exercise"]

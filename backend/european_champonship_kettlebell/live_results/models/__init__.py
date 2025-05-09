"""
Models package for the application.
"""

# Import constants first if they are needed by models during import
from .category import Category
from .constants import (
    AVAILABLE_DISCIPLINES,
    DISCIPLINE_NAMES,
    KB_SQUAT,
    ONE_KB_PRESS,
    # PISTOL_SQUAT,
    # SEE_SAW_PRESS,
    SNATCH,
    TGU,
    TWO_KB_PRESS,
)
from .player import Player
from .results.kb_squat_one_result import KBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult
from .results.overall import CategoryOverallResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult

# Import result models (adjust path if using results/ subdirectory)
from .results.snatch import SnatchResult
from .results.tgu import TGUResult
from .results.two_kettlebell_press_one_result import TwoKettlebellPressResult

# Import models
from .sport_club import SportClub


__all__ = [
    # Constants
    "AVAILABLE_DISCIPLINES",
    "DISCIPLINE_NAMES",
    "SNATCH",
    "TGU",
    # "SEE_SAW_PRESS",
    "KB_SQUAT",
    # "PISTOL_SQUAT",
    "ONE_KB_PRESS",
    "TWO_KB_PRESS",
    # Models
    "SportClub",
    "Category",
    "Player",
    "SnatchResult",
    "TGUResult",
    "PistolSquatResult",
    "SeeSawPressResult",
    "KBSquatResult",
    "OneKettlebellPressResult",
    "TwoKettlebellPressResult",
    "CategoryOverallResult",
]

"""
Models package for the application.
# ... (reszta docstring) ...
"""

# Import constants first if they are needed by models during import
from .category import Category
from .constants import (
    AVAILABLE_DISCIPLINES,
    DISCIPLINE_NAMES,
    KB_SQUAT,
    ONE_KB_PRESS,  # <--- NOWE STAŁE
    PISTOL_SQUAT,
    SEE_SAW_PRESS,
    SNATCH,
    TGU,
    TWO_KB_PRESS,
)
from .player import Player
from .results.kb_squat import KBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult  # <--- NOWY MODEL
from .results.overall import OverallResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult

# Import result models (adjust path if using results/ subdirectory)
from .results.snatch import BestSnatchResult, SnatchResult
from .results.tgu import TGUResult
from .results.two_kettlebell_press import TwoKettlebellPressResult  # <--- NOWE MODELE

# Import models
from .sport_club import SportClub

# Import service functions if they should be easily accessible (optional)
# from .services import update_discipline_positions, update_overall_results_for_category

# Define __all__ for explicit public interface of this package
__all__ = [
    # Constants
    "AVAILABLE_DISCIPLINES",
    "DISCIPLINE_NAMES",
    "SNATCH",
    "TGU",
    "SEE_SAW_PRESS",
    "KB_SQUAT",
    "PISTOL_SQUAT",
    "ONE_KB_PRESS",
    "TWO_KB_PRESS",  # <--- NOWE STAŁE
    # Models
    "SportClub",
    "Category",
    "Player",
    "SnatchResult",
    "TGUResult",
    "PistolSquatResult",
    "SeeSawPressResult",
    "BestSeeSawPressResult",
    "KBSquatResult",
    "BestKBSquatResult",
    "OneKettlebellPressResult",  # <--- NOWY MODEL
    "TwoKettlebellPressResult",
    "BestTwoKettlebellPressResult",  # <--- NOWE MODELE
    "OverallResult",
    # Services (optional)
    # 'update_discipline_positions',
    # 'update_overall_results_for_category',
]

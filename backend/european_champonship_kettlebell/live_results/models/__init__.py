# -*- coding: utf-8 -*-
"""
Models package for the application.

Imports all models from their respective files and makes them available
directly under app.models. Also exports constants.
"""

# Import constants first if they are needed by models during import
from .constants import (
    AVAILABLE_DISCIPLINES,
    SNATCH, TGU, SEE_SAW_PRESS, KB_SQUAT, PISTOL_SQUAT,
    DISCIPLINE_NAMES
)

# Import models
from .sport_club import SportClub
from .category import Category
from .player import Player

# Import result models (adjust path if using results/ subdirectory)
from .results.snatch import SnatchResult
from .results.tgu import TGUResult
from .results.pistol_squat import PistolSquatResult
from .results.see_saw_press import SeeSawPressResult, BestSeeSawPressResult
from .results.kb_squat import KBSquatResult, BestKBSquatResult
from .results.overall import OverallResult

# Import service functions if they should be easily accessible (optional)
# from .services import update_discipline_positions, update_overall_results_for_category

# Define __all__ for explicit public interface of this package
__all__ = [
    # Constants
    'AVAILABLE_DISCIPLINES', 'DISCIPLINE_NAMES',
    'SNATCH', 'TGU', 'SEE_SAW_PRESS', 'KB_SQUAT', 'PISTOL_SQUAT',

    # Models
    'SportClub',
    'Category',
    'Player',
    'SnatchResult',
    'TGUResult',
    'PistolSquatResult',
    'SeeSawPressResult', 'BestSeeSawPressResult',
    'KBSquatResult', 'BestKBSquatResult',
    'OverallResult',

    # Services (optional)
    # 'update_discipline_positions',
    # 'update_overall_results_for_category',
]
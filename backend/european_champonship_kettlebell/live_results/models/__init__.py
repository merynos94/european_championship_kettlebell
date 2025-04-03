# -*- coding: utf-8 -*-
"""
Models package for the application.
# ... (reszta docstring) ...
"""

# Import constants first if they are needed by models during import
from .constants import (
    AVAILABLE_DISCIPLINES,
    SNATCH, TGU, SEE_SAW_PRESS, KB_SQUAT, PISTOL_SQUAT,
    ONE_KB_PRESS, TWO_KB_PRESS, # <--- NOWE STAŁE
    DISCIPLINE_NAMES
)

# Import models
from .sport_club import SportClub
from .category import Category
from .player import Player

# Import result models (adjust path if using results/ subdirectory)
from .results.snatch import SnatchResult, BestSnatchResult
from .results.tgu import TGUResult, BestTGUResult
from .results.pistol_squat import PistolSquatResult, BestPistolSquatResult
from .results.see_saw_press import SeeSawPressResult, BestSeeSawPressResult
from .results.kb_squat import KBSquatResult, BestKBSquatResult
from .results.one_kettlebell_press import OneKettlebellPressResult, BestOneKettlebellPressResult # <--- NOWY MODEL
from .results.two_kettlebell_press import TwoKettlebellPressResult, BestTwoKettlebellPressResult # <--- NOWE MODELE
from .results.overall import OverallResult

# Import service functions if they should be easily accessible (optional)
# from .services import update_discipline_positions, update_overall_results_for_category

# Define __all__ for explicit public interface of this package
__all__ = [
    # Constants
    'AVAILABLE_DISCIPLINES', 'DISCIPLINE_NAMES',
    'SNATCH', 'TGU', 'SEE_SAW_PRESS', 'KB_SQUAT', 'PISTOL_SQUAT',
    'ONE_KB_PRESS', 'TWO_KB_PRESS', # <--- NOWE STAŁE

    # Models
    'SportClub',
    'Category',
    'Player',
    'SnatchResult',
    'TGUResult',
    'PistolSquatResult',
    'SeeSawPressResult', 'BestSeeSawPressResult',
    'KBSquatResult', 'BestKBSquatResult',
    'OneKettlebellPressResult', # <--- NOWY MODEL
    'TwoKettlebellPressResult', 'BestTwoKettlebellPressResult', # <--- NOWE MODELE
    'OverallResult',

    # Services (optional)
    # 'update_discipline_positions',
    # 'update_overall_results_for_category',
]
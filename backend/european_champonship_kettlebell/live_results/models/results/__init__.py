# -*- coding: utf-8 -*-

# Importuj surowe wyniki
from .snatch import SnatchResult
from .tgu import TGUResult
from .pistol_squat import PistolSquatResult
from .see_saw_press import SeeSawPressResult
from .kb_squat import KBSquatResult
from .one_kettlebell_press import OneKettlebellPressResult # Dodano
from .two_kettlebell_press import TwoKettlebellPressResult # Dodano

# Importuj najlepsze wyniki (zakładając, że są w osobnych plikach lub w tych samych co surowe)
# Dostosuj ścieżki, jeśli Best* są w tych samych plikach co surowe wyniki
from .snatch import BestSnatchResult               # Dodano
from .tgu import BestTGUResult                     # Dodano
from .pistol_squat import BestPistolSquatResult    # Dodano
from .see_saw_press import BestSeeSawPressResult        # Już było
from .kb_squat import BestKBSquatResult                 # Już było
from .one_kettlebell_press import BestOneKettlebellPressResult # Dodano
from .two_kettlebell_press import BestTwoKettlebellPressResult        # Dodano (zakładając, że jest w two_kettlebell_press.py)

# Importuj wynik ogólny
from .overall import OverallResult


# Lista modeli eksportowanych przez ten moduł
__all__ = [
    # Surowe wyniki
    'SnatchResult',
    'TGUResult',
    'PistolSquatResult',
    'SeeSawPressResult',
    'KBSquatResult',
    'OneKettlebellPressResult',
    'TwoKettlebellPressResult',

    # Najlepsze wyniki
    'BestSnatchResult',
    'BestTGUResult',
    'BestPistolSquatResult',
    'BestSeeSawPressResult',
    'BestKBSquatResult',
    'BestOneKettlebellPressResult',
    'BestTwoKettlebellPressResult',

    # Wynik ogólny
    'OverallResult',
]
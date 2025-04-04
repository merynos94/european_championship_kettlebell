# Importuj surowe wyniki
from .kb_squat import (
    BestKBSquatResult,  # Już było
    KBSquatResult,
)
from .one_kettlebell_press import (
    # Dodano
    OneKettlebellPressResult,  # Dodano
)

# Importuj wynik ogólny
from .overall import OverallResult
from .pistol_squat import (
    PistolSquatResult,
)
from .see_saw_press import (
    BestSeeSawPressResult,  # Już było
    SeeSawPressResult,
)

# Importuj najlepsze wyniki (zakładając, że są w osobnych plikach lub w tych samych co surowe)
# Dostosuj ścieżki, jeśli Best* są w tych samych plikach co surowe wyniki
from .snatch import (
    BestSnatchResult,  # Dodano
    SnatchResult,
)
from .tgu import (
    # Dodano
    TGUResult,
)
from .two_kettlebell_press import (
    BestTwoKettlebellPressResult,  # Dodano (zakładając, że jest w two_kettlebell_press.py)
    TwoKettlebellPressResult,  # Dodano
)

# Lista modeli eksportowanych przez ten moduł
__all__ = [
    # Surowe wyniki
    "SnatchResult",
    "TGUResult",
    "PistolSquatResult",
    "SeeSawPressResult",
    "KBSquatResult",
    "OneKettlebellPressResult",
    "TwoKettlebellPressResult",
    # Najlepsze wyniki
    "BestSnatchResult",
    "BestPistolSquatResult",
    "BestSeeSawPressResult",
    "BestKBSquatResult",
    "BestTwoKettlebellPressResult",
    # Wynik ogólny
    "OverallResult",
]

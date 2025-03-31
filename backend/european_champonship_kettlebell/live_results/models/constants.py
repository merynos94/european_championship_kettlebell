# -*- coding: utf-8 -*-
"""Constants related to disciplines."""

# Discipline constants
SNATCH: str = "snatch"
TGU: str = "tgu"
SEE_SAW_PRESS: str = "see_saw_press"
KB_SQUAT: str = "kb_squat"
PISTOL_SQUAT: str = "pistol_squat"
ONE_KB_PRESS: str = "one_kettlebell_press" # <--- NOWE
TWO_KB_PRESS: str = "two_kettlebell_press" # <--- NOWE

# Tuples for choices fields or other uses
AVAILABLE_DISCIPLINES: list[tuple[str, str]] = [
    (SNATCH, "Snatch"),
    (TGU, "Turkish Get-Up"),
    (SEE_SAW_PRESS, "See Saw Press"),
    (KB_SQUAT, "Kettlebell Squat"),
    (PISTOL_SQUAT, "Pistol Squat"),
    (ONE_KB_PRESS, "One Kettlebell Press"), # <--- NOWE
    (TWO_KB_PRESS, "Two Kettlebell Press"), # <--- NOWE
]

DISCIPLINE_NAMES: dict[str, str] = dict(AVAILABLE_DISCIPLINES)
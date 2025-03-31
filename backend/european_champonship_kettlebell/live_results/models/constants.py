# -*- coding: utf-8 -*-
"""Constants related to disciplines."""

# Discipline constants
SNATCH: str = "snatch"
TGU: str = "tgu"
SEE_SAW_PRESS: str = "see_saw_press"
KB_SQUAT: str = "kb_squat"
PISTOL_SQUAT: str = "pistol_squat"

# Tuples for choices fields or other uses
AVAILABLE_DISCIPLINES: list[tuple[str, str]] = [
    (SNATCH, "Snatch"),
    (TGU, "Turkish Get-Up"),
    (SEE_SAW_PRESS, "See Saw Press"),
    (KB_SQUAT, "Kettlebell Squat"),
    (PISTOL_SQUAT, "Pistol Squat"),
]

DISCIPLINE_NAMES: dict[str, str] = dict(AVAILABLE_DISCIPLINES)
"""Constants related to disciplines."""

# Discipline constants
SNATCH: str = "snatch"
TGU: str = "tgu"
KB_SQUAT: str = "kb_squat"
ONE_KB_PRESS: str = "one_kettlebell_press"
TWO_KB_PRESS: str = "two_kettlebell_press"

# Tuples for choices fields or other uses
AVAILABLE_DISCIPLINES: list[tuple[str, str]] = [
    (SNATCH, "Snatch"),
    (TGU, "Turkish Get-Up"),
    (KB_SQUAT, "Kettlebell Squat"),
    (ONE_KB_PRESS, "One Kettlebell Press"),
    (TWO_KB_PRESS, "Two Kettlebell Press"),
]

DISCIPLINE_NAMES: dict[str, str] = dict(AVAILABLE_DISCIPLINES)

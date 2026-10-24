"""Food diary categories and autocomplete groups (constitution D2) — single source of truth."""

FOOD_CATEGORIES: tuple[str, ...] = (
    "breakfast",
    "morning_snack",
    "lunch",
    "afternoon_snack",
    "dinner",
    "after_dinner",
    "unassigned",
)
MEDS_CATEGORIES: tuple[str, ...] = ("medication", "supplement")
SPORT_CATEGORIES: tuple[str, ...] = ("sport",)
NOTE_CATEGORIES: tuple[str, ...] = ("note",)

ALL_CATEGORIES: tuple[str, ...] = FOOD_CATEGORIES + MEDS_CATEGORIES + SPORT_CATEGORIES + NOTE_CATEGORIES

# Autocomplete group per category; None = no autocomplete (notes).
CATEGORY_GROUP: dict[str, str | None] = {
    **{c: "food" for c in FOOD_CATEGORIES},
    **{c: "meds" for c in MEDS_CATEGORIES},
    **{c: "sport" for c in SPORT_CATEGORIES},
    **{c: None for c in NOTE_CATEGORIES},
}

# No unit means pieces ("ks").
UNITS: tuple[str, ...] = ("ks", "l", "ml", "g", "kg")
MED_KINDS: tuple[str, ...] = ("medication", "supplement")

TEXT_MAX_LENGTH = 200
INTENSITY_MIN, INTENSITY_MAX = 1, 5
SLEEP_QUALITY_MIN, SLEEP_QUALITY_MAX = 1, 3
DIGESTION_MIN, DIGESTION_MAX = 1, 10  # stool, gas

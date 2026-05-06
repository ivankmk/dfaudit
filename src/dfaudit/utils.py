"""Style tokens, color palettes, and audit conventions for dfaudit."""

from typing import TypedDict

# String values treated as missing beyond isna()
STRING_SENTINELS: frozenset[str] = frozenset({
    "", "n/a", "na", "null", "none", "nan", "nil",
    "-", "--", "?", "unknown", "missing", "not available", "not applicable",
})

# Numeric values commonly used as missing sentinels in legacy data
NUMERIC_SENTINELS: frozenset[int | float] = frozenset({-999, -9999, 9999, 99999})


class OverviewColors(TypedDict, total=False):
    header: str
    missing_data: str
    highlight: str
    df_bg: str
    text: str
    grid: str
    muted: str


STYLES: dict[str, OverviewColors] = {
    "vivid": {
        "header": "#1d2d44",
        "missing_data": "#bc4749",
        "soft_missing_data": "#F9B2D7",
        "highlight": "#5E7AC4",
        "df_bg": "#0d1321",
        "text": "#f1faee",
        "grid": "#f1faee",
        "muted": "#9aa7b5",
    },
}

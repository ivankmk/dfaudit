"""Color palettes and style tokens for the dataframe overview table."""

from typing import TypedDict


class OverviewColors(TypedDict, total=False):
    """Color keys used by the overview table styler."""

    header: str
    missing_data: str
    df_bg: str
    text: str
    grid: str
    muted: str


DEFAULT_OVERVIEW_COLORS: OverviewColors = {
    "header": "#457b9d",
    "missing_data": "#e63946",
    "df_bg": "#1d3557",
    "text": "#f1faee",
    "grid": "#f1faee",
    "muted": "#9aa7b5",
}

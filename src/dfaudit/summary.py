"""High-level API for dataframe auditing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .utils import NUMERIC_SENTINELS, STRING_SENTINELS, STYLES

if TYPE_CHECKING:
    from pandas.io.formats.style import Styler


def _count_soft_missing(col: pd.Series) -> int:
    """Count non-null values that look like missing: sentinels, empty/whitespace strings."""
    not_na = col.notna()
    if pd.api.types.is_numeric_dtype(col):
        return int((not_na & col.isin(NUMERIC_SENTINELS)).sum())
    if pd.api.types.is_object_dtype(col) or pd.api.types.is_string_dtype(col):
        normalized = col.astype(str).str.strip().str.lower().where(not_na)
        str_sentinel = normalized.isin(STRING_SENTINELS)
        num_sentinel = col.isin(NUMERIC_SENTINELS)
        return int((not_na & (str_sentinel | num_sentinel)).sum())
    return 0


def _compute(dataframe: pd.DataFrame) -> pd.DataFrame:
    cols = list(dataframe.columns)
    n = len(dataframe)

    rows = []
    for c in cols:
        col = dataframe[c]
        vc = col.value_counts(normalize=True)
        mode_val = vc.index[0] if len(vc) > 0 else None
        soft = _count_soft_missing(col)

        rows.append({
            "column": c,
            "dtype": str(col.dtype),
            "missing": int(col.isna().sum()),
            "missing_pct": float(col.isna().mean() * 100),
            "soft_missing": soft,
            "soft_missing_pct": float(soft / n * 100) if n > 0 else 0.0,
            "unique": int(col.nunique(dropna=True)),
            "unique_pct": float(col.nunique(dropna=True) / n * 100) if n > 0 else 0.0,
            "mode": mode_val,
            "mode_pct": float(vc.iloc[0] * 100) if len(vc) > 0 else 0.0,
            "top3_pct": {str(k): f"{v * 100:.1f}%" for k, v in vc.head(3).items()}
        })

    return (
        pd.DataFrame(rows)
        .sort_values(["missing_pct", "unique"], ascending=[False, False])
        .reset_index(drop=True)
    )


def overview(
    dataframe: pd.DataFrame,
    *,
    style: str = "default",
) -> Styler:
    """Return a styled pandas table summarising the dataframe column by column.

    Columns reported: dtype, missing count and %, soft-missing count and % (sentinels
    and whitespace-only strings that pandas does not count as null), unique count and %,
    mode value and %, top-3 values with their frequencies.
    Rows sorted by missing % descending, then unique count descending.

    Args:
        dataframe: Input dataframe to audit.
        style: Named style from STYLES — "vivid" (dark), "light", or "default" (no custom styling).
    """
    colors = STYLES.get(style)
    data = _compute(dataframe)
    pct_cols = [c for c in data.columns if c.endswith("_pct") and c != "top3_pct"]
    fmt = {"missing": "{:,.0f}", "soft_missing": "{:,.0f}", "unique": "{:,.0f}"}
    fmt |= {c: "{:.1f}%" for c in pct_cols}
    c = colors or {}
    bar_cols = ["missing_pct", "soft_missing_pct", "unique_pct"]
    styler = (
        data.style.format(fmt)
        .bar(subset=["missing_pct"], color=c.get("missing_data", "#bc4749"), vmin=0, vmax=100)
        .bar(subset=["soft_missing_pct"], color=c.get("soft_missing_data", "#F9B2D7"), vmin=0, vmax=100)
        .bar(subset=["unique_pct"], color=c.get("highlight", "#5e7ac4"))
        .set_properties(subset=bar_cols, **{"width": "90px", "min-width": "90px", "max-width": "90px"})
    )

    if colors:
        border = f"1px solid {colors['grid']}"
        styler = (
            styler
            .set_properties(**{"background-color": colors["df_bg"], "color": colors["text"], "border": border})
            .set_table_styles(
                [
                    {"selector": "th", "props": [
                        ("background-color", colors["header"]),
                        ("color", colors["text"]),
                        ("border", border),
                    ]},
                ]
            )
        )

    return styler

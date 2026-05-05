"""High-level API for dataframe auditing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

from .styles import DEFAULT_OVERVIEW_COLORS, OverviewColors

if TYPE_CHECKING:
    from pandas.io.formats.style import Styler


def _style_overview_frame(
    profile: pd.DataFrame,
    *,
    colors: OverviewColors,
    caption: str,
) -> Styler:
    c = colors
    styler = profile.style
    styler = styler.format(
        {
            "missing_pct": "{:.1f}%",
            "missing": "{:,.0f}",
            "unique_values": "{:,.0f}",
        }
    )
    styler = styler.bar(subset=["missing_pct"], color=c["missing_data"])
    border = f"1px solid {c['grid']}"
    styler = styler.set_properties(
        **{
            "background-color": c["df_bg"],
            "color": c["text"],
            "border": border,
        }
    )
    styler = styler.set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", c["header"]),
                    ("color", c["text"]),
                    ("border", border),
                ],
            },
            {
                "selector": "caption",
                "props": [
                    ("caption-side", "top"),
                    ("color", c["text"]),
                    ("font-weight", "bold"),
                ],
            },
        ]
    )
    return styler.set_caption(caption)


def compute_overview(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Build a per-column summary table (dtype, missingness, uniques, sample)."""

    cols = list(dataframe.columns)
    profile = pd.DataFrame(
        {
            "column": cols,
            "dtype": [str(dataframe[c].dtype) for c in cols],
            "missing": [int(dataframe[c].isna().sum()) for c in cols],
            "missing_pct": [float(dataframe[c].isna().mean() * 100) for c in cols],
            "unique_values": [int(dataframe[c].nunique(dropna=True)) for c in cols],
            "sample_value": [
                dataframe[c].dropna().iloc[0]
                if dataframe[c].notna().any()
                else None
                for c in cols
            ],
        }
    )
    return profile.sort_values(
        ["missing_pct", "unique_values"], ascending=[False, False]
    ).reset_index(drop=True)


def style_overview(
    dataframe: pd.DataFrame,
    *,
    colors: OverviewColors | None = None,
    caption: str = "Data overview",
) -> Styler:
    """Return a pandas Styler for a dark-themed overview of ``dataframe``."""

    merged: OverviewColors = {**DEFAULT_OVERVIEW_COLORS, **(colors or {})}
    profile = compute_overview(dataframe)
    return _style_overview_frame(profile, colors=merged, caption=caption)


@dataclass
class AuditReport:
    """Container for audit outputs."""

    dataframe: pd.DataFrame
    overview: pd.DataFrame

    def to_styler(
        self,
        *,
        colors: OverviewColors | None = None,
        caption: str = "Data overview",
    ) -> Styler:
        """Styled overview matching :func:`style_overview` for this report."""

        merged: OverviewColors = {**DEFAULT_OVERVIEW_COLORS, **(colors or {})}
        return _style_overview_frame(self.overview, colors=merged, caption=caption)


def profile(dataframe: pd.DataFrame) -> AuditReport:
    """Build an audit report with a computed overview table."""

    return AuditReport(
        dataframe=dataframe,
        overview=compute_overview(dataframe),
    )

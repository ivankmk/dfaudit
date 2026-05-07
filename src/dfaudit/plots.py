"""Audit visualizations for dfaudit."""

from __future__ import annotations

import base64
import io

import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure

from .utils import STYLES


class _HTMLFigure:
    """Wraps a matplotlib Figure so Jupyter renders it without %matplotlib inline."""

    def __init__(self, fig: Figure) -> None:
        self._fig = fig

    def _repr_html_(self) -> str:
        buf = io.BytesIO()
        self._fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode()
        return f'<img src="data:image/png;base64,{encoded}"/>'

    def savefig(self, *args, **kwargs) -> None:
        self._fig.savefig(*args, **kwargs)


def missing_matrix(
    dataframe: pd.DataFrame,
    *,
    style: str = "default",
    figsize: tuple[int, int] | None = None,
) -> _HTMLFigure:
    """Render a two-panel missingness matrix for the dataframe.

    Left panel: barcode view — each column is a row, each pixel a data point,
    red means missing. Columns ordered by missing % ascending (most missing on top).
    Right panel: horizontal bar chart of missing % per column, scaled 0–100%.

    Args:
        dataframe: Input dataframe to audit.
        style: Named style from STYLES — "vivid" (dark), "light", or "default" (matplotlib defaults).
        figsize: Figure size as (width, height). Auto-scales height by column count if not set.
    """
    colors = STYLES.get(style)
    c_missing = colors.get("missing_data", "#bc4749") if colors else "#bc4749"
    c_present = colors.get("df_bg", "#e8edf2") if colors else "#e8edf2"
    c_text    = colors.get("text", "#1d2d44") if colors else "#1d2d44"
    c_bg      = colors.get("df_bg", "white") if colors else "white"
    c_grid    = colors.get("grid", "#cccccc") if colors else "#cccccc"

    miss_pct = dataframe.isna().mean() * 100
    order = miss_pct.sort_values(ascending=True).index.tolist()
    miss = dataframe[order].isna().to_numpy().T

    size = figsize or (14, max(4, len(order) * 0.4 + 2))
    fig = Figure(figsize=size, constrained_layout=True)
    fig.patch.set_facecolor(c_bg)

    gs = fig.add_gridspec(1, 2, width_ratios=[3.25, 1.1])
    ax     = fig.add_subplot(gs[0])
    ax_bar = fig.add_subplot(gs[1], sharey=ax)

    for a in (ax, ax_bar):
        a.set_facecolor(c_bg)

    ax.imshow(miss, aspect="auto", interpolation="nearest", cmap=ListedColormap([c_present, c_missing]))
    ax.set_yticks(np.arange(len(order)), order, color=c_text)
    xticks = np.linspace(0, len(dataframe) - 1, min(6, len(dataframe)), dtype=int)
    ax.set_xticks(xticks, [f"{x:,}" for x in xticks], color=c_text)
    ax.set_xlabel("Row Index", color=c_text)
    ax.set_title("Missingness Matrix", loc="left", pad=12, color=c_text)
    ax.tick_params(colors=c_text)
    ax.hlines(
        np.arange(0.5, len(order) - 0.5),
        xmin=-0.5, xmax=len(dataframe) - 0.5,
        color=c_grid, alpha=0.25, linewidth=0.8,
    )
    ax.grid(False)
    ax.spines[:].set_visible(False)

    ax_bar.barh(np.arange(len(order)), miss_pct.reindex(order), color=c_missing, alpha=0.9)
    ax_bar.set_xlabel("Missing Percentage", color=c_text)
    ax_bar.set_xlim(0, 100)
    ax_bar.tick_params(axis="y", left=False, labelleft=False)
    ax_bar.tick_params(axis="x", colors=c_text)
    ax_bar.xaxis.grid(True, color=c_grid, alpha=0.25, linewidth=0.8)
    ax_bar.set_axisbelow(True)
    ax_bar.spines[:].set_visible(False)

    for i, val in enumerate(miss_pct.reindex(order)):
        if val > 0:
            ax_bar.text(val + 0.6, i, f"{val:.1f}%", va="center", fontsize=9, color=c_text)

    return _HTMLFigure(fig)

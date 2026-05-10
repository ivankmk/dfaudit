"""Audit visualizations for dfaudit."""

from __future__ import annotations

import base64
import io

import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from .utils import STYLES

# Palette for categorical coloring (up to MAX_COLORS distinct values per column)
_CAT_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]
MAX_COLORS = len(_CAT_PALETTE)  # 10
_OVERFLOW_COLOR = "#cccccc"     # high-cardinality / "too many uniques"


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


def unique_matrix(
    dataframe: pd.DataFrame,
    *,
    style: str = "default",
    figsize: tuple[int, int] | None = None,
    max_colors: int = MAX_COLORS,
) -> _HTMLFigure:
    """Render a unique-value matrix for the dataframe.

    Left panel: barcode view — each column is a row, each pixel a data point,
    colored by which unique value it holds. Columns with more unique values than
    ``max_colors`` are rendered in a single overflow color.
    Right panel: bar chart of unique value count per column.

    Args:
        dataframe: Input dataframe to audit.
        style: Named style from STYLES — "vivid" (dark), "light", or "default".
        figsize: Figure size as (width, height). Auto-scales by column count if not set.
        max_colors: Columns with unique count ≤ this get distinct colors; others get overflow color.
    """
    colors = STYLES.get(style)
    c_text     = colors.get("text", "#1d2d44") if colors else "#1d2d44"
    c_bg       = colors.get("df_bg", "white") if colors else "white"
    c_grid     = colors.get("grid", "#cccccc") if colors else "#cccccc"
    c_overflow = _OVERFLOW_COLOR

    n_cols = len(dataframe.columns)
    order = dataframe.columns.tolist()

    # Build integer matrix: each row = a column, each position = color index (0-based)
    # NaN → -1 (rendered transparent / as background)
    matrix = np.full((n_cols, len(dataframe)), -1, dtype=int)
    col_palettes: list[list[str]] = []
    col_n_unique: list[int] = []

    for i, col in enumerate(order):
        series = dataframe[col]
        unique_vals = series.dropna().unique()
        n_unique = len(unique_vals)
        col_n_unique.append(n_unique)

        if n_unique <= max_colors:
            val_to_idx = {v: j for j, v in enumerate(unique_vals)}
            palette = _CAT_PALETTE[:n_unique]
            col_palettes.append(palette)
            for row_idx, val in enumerate(series):
                if pd.isna(val):
                    matrix[i, row_idx] = -1
                else:
                    matrix[i, row_idx] = val_to_idx[val]
        else:
            # all non-null cells get index 0 → overflow color
            col_palettes.append([c_overflow])
            for row_idx, val in enumerate(series):
                if not pd.isna(val):
                    matrix[i, row_idx] = 0

    # Build solid RGB image: shape (n_cols, n_rows, 3)
    def _hex_to_rgb(h: str) -> np.ndarray:
        h = h.lstrip("#")
        return np.array([int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)])

    bg_rgb = _hex_to_rgb(c_bg if c_bg != "white" else "#ffffff")
    img = np.tile(bg_rgb, (n_cols, len(dataframe), 1))

    for i, palette in enumerate(col_palettes):
        palette_rgb = np.array([_hex_to_rgb(c) for c in palette])
        row = matrix[i]
        for color_idx, rgb in enumerate(palette_rgb):
            mask = row == color_idx
            img[i, mask] = rgb

    size = figsize or (14, max(4, n_cols * 0.4 + 2))
    fig = Figure(figsize=size, constrained_layout=True)
    fig.patch.set_facecolor(c_bg)

    gs = fig.add_gridspec(1, 2, width_ratios=[3.25, 1.1])
    ax     = fig.add_subplot(gs[0])
    ax_bar = fig.add_subplot(gs[1], sharey=ax)

    for a in (ax, ax_bar):
        a.set_facecolor(c_bg)

    ax.imshow(img, aspect="auto", interpolation="nearest")

    ax.set_yticks(np.arange(n_cols), order, color=c_text)
    xticks = np.linspace(0, len(dataframe) - 1, min(6, len(dataframe)), dtype=int)
    ax.set_xticks(xticks, [f"{x:,}" for x in xticks], color=c_text)
    ax.set_xlabel("Row Index", color=c_text)
    ax.set_title("Unique Value Matrix", loc="left", pad=12, color=c_text)
    ax.tick_params(colors=c_text)
    ax.hlines(
        np.arange(0.5, n_cols - 0.5),
        xmin=-0.5, xmax=len(dataframe) - 0.5,
        color=c_grid, alpha=0.25, linewidth=0.8,
    )
    ax.grid(False)
    ax.spines[:].set_visible(False)

    # Right panel: unique count bar chart
    bar_colors = [
        c_overflow if n > max_colors else _CAT_PALETTE[min(n - 1, max_colors - 1)]
        for n in col_n_unique
    ]
    ax_bar.barh(np.arange(n_cols), col_n_unique, color=bar_colors, alpha=0.9)
    ax_bar.set_xlabel("Unique Values", color=c_text)
    ax_bar.tick_params(axis="y", left=False, labelleft=False)
    ax_bar.tick_params(axis="x", colors=c_text)
    ax_bar.xaxis.grid(True, color=c_grid, alpha=0.25, linewidth=0.8)
    ax_bar.set_axisbelow(True)
    ax_bar.spines[:].set_visible(False)
    for i, val in enumerate(col_n_unique):
        ax_bar.text(val + 0.2, i, str(val), va="center", fontsize=9, color=c_text)

    # Legend: show color → value mapping for low-cardinality columns
    legend_handles = []
    seen: dict[str, str] = {}
    for col, palette, n_unique in zip(order, col_palettes, col_n_unique):
        if n_unique > max_colors:
            key = f"{col}: {n_unique} uniques (overflow)"
            if key not in seen:
                seen[key] = c_overflow
                legend_handles.append(Patch(color=c_overflow, label=key))
        else:
            unique_vals = dataframe[col].dropna().unique()
            for j, (val, hex_color) in enumerate(zip(unique_vals, palette)):
                key = f"{col}={val}"
                if key not in seen:
                    seen[key] = hex_color
                    legend_handles.append(Patch(color=hex_color, label=key))

    if legend_handles:
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.12),
            ncol=min(6, len(legend_handles)),
            fontsize=8,
            frameon=False,
            labelcolor=c_text,
        )

    return _HTMLFigure(fig)

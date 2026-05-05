"""Runtime configuration (non-visual defaults)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Visual theme options used by plotting functions."""

    palette: str = "modern"
    grid: bool = True
    dpi: int = 120

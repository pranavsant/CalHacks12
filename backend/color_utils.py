# backend/color_utils.py
"""
Color normalization utilities for pen control.

Restricts all drawing colors to exactly two options:
- BLACK (#000000)
- BLUE (#0000FF)
- PEN_UP ("none") - for pen-up (no drawing)

This ensures compatibility with dual-pen robot systems that support only black and blue inks.
"""

from __future__ import annotations
from typing import Optional

# Allowed drawing colors
BLACK = "#000000"
BLUE  = "#0000FF"
PEN_UP = "none"


def _parse_hex_color(c: str) -> Optional[tuple[int, int, int]]:
    """
    Parse #RRGGBB into (R,G,B); tolerate case; return None if invalid.

    Args:
        c: Color string to parse (hex or named)

    Returns:
        Tuple of (R, G, B) integers, or None if invalid/pen-up
    """
    if not isinstance(c, str):
        return None
    c = c.strip()
    if c.lower() == PEN_UP:
        return None
    if c.startswith("#") and len(c) == 7:
        try:
            r = int(c[1:3], 16)
            g = int(c[3:5], 16)
            b = int(c[5:7], 16)
            return (r, g, b)
        except Exception:
            return None
    # Map common named colors
    name = c.lower()
    NAMED = {
        "black": (0, 0, 0),
        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "white": (255, 255, 255),
        "yellow": (255, 255, 0),
        "cyan": (0, 255, 255),
        "magenta": (255, 0, 255),
    }
    return NAMED.get(name)


def _dist2(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """
    Compute squared Euclidean distance between two RGB colors.

    Args:
        a: First RGB tuple
        b: Second RGB tuple

    Returns:
        Squared distance (integer)
    """
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return dr*dr + dg*dg + db*db


def normalize_draw_color(color: Optional[str]) -> str:
    """
    Map any input color to one of:
      - 'none' (pen up) if explicitly requested
      - '#0000FF' (blue) or '#000000' (black) for any drawing color

    Rule: if color parses and is closer to BLUE than BLACK in RGB, choose BLUE; else BLACK.
    If color is missing/invalid, default to BLACK.

    Args:
        color: Input color string (hex, named, or "none")

    Returns:
        One of: "none", "#000000", or "#0000FF"

    Examples:
        >>> normalize_draw_color("none")
        'none'
        >>> normalize_draw_color("#FF0000")  # Red -> closer to black
        '#000000'
        >>> normalize_draw_color("#0000FF")  # Blue
        '#0000FF'
        >>> normalize_draw_color("blue")
        '#0000FF'
        >>> normalize_draw_color("#FF4500")  # OrangeRed -> closer to black
        '#000000'
    """
    # Pen up preserved as-is
    if isinstance(color, str) and color.strip().lower() == PEN_UP:
        return PEN_UP

    rgb = _parse_hex_color(color) if isinstance(color, str) else None
    if rgb is None:
        # No valid color → default black
        return BLACK

    # Choose nearest of two anchors in squared RGB distance
    d_black = _dist2(rgb, (0, 0, 0))
    d_blue  = _dist2(rgb, (0, 0, 255))
    return BLUE if d_blue < d_black else BLACK

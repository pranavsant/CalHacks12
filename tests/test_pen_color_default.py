"""
Test pen color logic and defaults.

Verifies that pen colors are correctly normalized when transforming curves to relative format.
All colors are now automatically normalized to black (#000000), blue (#0000FF), or pen-up (none).
"""

import pytest
from backend.schemas import CurveDef, PenSpec
from backend.utils_relative import wrap_to_relative
from backend.color_utils import BLACK, BLUE, PEN_UP


def test_curve_with_explicit_color():
    """Test that explicit colors are normalized (red -> black)."""
    curve = CurveDef(
        name="red_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="#FF0000"
    )

    start_pose = (0.0, 0.0, 0.0)
    rel_curve = wrap_to_relative(start_pose, curve)

    # Red is normalized to black (closer to black than blue)
    assert rel_curve.pen.color == BLACK


def test_curve_without_color_uses_default():
    """Test that curves without color get a default color."""
    curve = CurveDef(
        name="uncolored_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color=None
    )

    start_pose = (0.0, 0.0, 0.0)
    # No explicit default, should use function's default
    rel_curve = wrap_to_relative(start_pose, curve)

    # Should get black as default
    assert rel_curve.pen.color == BLACK


def test_curve_with_custom_default_color():
    """Test that custom default colors are normalized (green -> black)."""
    curve = CurveDef(
        name="uncolored_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color=None
    )

    start_pose = (0.0, 0.0, 0.0)
    custom_default = "#00FF00"  # Green

    rel_curve = wrap_to_relative(start_pose, curve, default_color=custom_default)

    # Green is normalized to black (closer to black than blue)
    assert rel_curve.pen.color == BLACK


def test_pen_up_with_none_color():
    """Test that 'none' color indicates pen up (no drawing)."""
    curve = CurveDef(
        name="travel_move",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color=None
    )

    start_pose = (0.0, 0.0, 0.0)
    # Explicitly set default to "none" for pen-up moves
    rel_curve = wrap_to_relative(start_pose, curve, default_color="none")

    # Should have "none" to indicate pen up
    assert rel_curve.pen.color.lower() == "none"


def test_multiple_curves_with_different_colors():
    """Test that multiple curves get normalized colors."""
    curves_and_colors = [
        ("curve1", "#FF0000"),  # Red -> black
        ("curve2", "#00FF00"),  # Green -> black
        ("curve3", "#0000FF"),  # Blue -> blue
        ("curve4", None),       # No color, should get default black
    ]

    start_pose = (0.0, 0.0, 0.0)
    rel_curves = []

    for name, color in curves_and_colors:
        curve = CurveDef(
            name=name,
            x="t",
            y="0",
            t_min=0.0,
            t_max=1.0,
            color=color
        )
        rel_curve = wrap_to_relative(start_pose, curve)
        rel_curves.append(rel_curve)

    # Verify colors are normalized
    assert rel_curves[0].pen.color == BLACK  # Red normalized to black
    assert rel_curves[1].pen.color == BLACK  # Green normalized to black
    assert rel_curves[2].pen.color == BLUE   # Blue stays blue
    assert rel_curves[3].pen.color == BLACK  # Default black


def test_named_colors():
    """Test that named colors are normalized."""
    curve = CurveDef(
        name="named_color_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="red"  # Named color instead of hex
    )

    start_pose = (0.0, 0.0, 0.0)
    rel_curve = wrap_to_relative(start_pose, curve)

    # "red" should be normalized to black
    assert rel_curve.pen.color == BLACK


def test_pen_spec_validation():
    """Test that PenSpec normalizes all colors."""
    # Arbitrary hex color -> normalized to blue
    pen1 = PenSpec(color="#ABCDEF")
    assert pen1.color == BLUE  # Light blue-ish -> blue

    # "none" for pen up
    pen2 = PenSpec(color="none")
    assert pen2.color == PEN_UP

    # Named color "blue" -> normalized to #0000FF
    pen3 = PenSpec(color="blue")
    assert pen3.color == BLUE


def test_color_override_precedence():
    """Test that curve color takes precedence over default (but both are normalized)."""
    curve = CurveDef(
        name="colored_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="#123456"  # Dark blue-ish
    )

    start_pose = (0.0, 0.0, 0.0)
    default_color = "#FEDCBA"  # Light pinkish

    rel_curve = wrap_to_relative(start_pose, curve, default_color=default_color)

    # Both would normalize to black, but curve's color takes precedence before normalization
    # #123456 is dark and closer to black
    assert rel_curve.pen.color == BLACK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

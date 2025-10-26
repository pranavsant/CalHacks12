"""
Test pen color logic and defaults.

Verifies that pen colors are correctly preserved or defaulted when
transforming curves to relative format.
"""

import pytest
from backend.schemas import CurveDef, PenSpec
from backend.utils_relative import wrap_to_relative


def test_curve_with_explicit_color():
    """Test that explicit colors from absolute curves are preserved."""
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

    # Should preserve the original color
    assert rel_curve.pen.color == "#FF0000"


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
    assert rel_curve.pen.color == "#000000"


def test_curve_with_custom_default_color():
    """Test that custom default colors are applied correctly."""
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

    # Should use the custom default
    assert rel_curve.pen.color == custom_default


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
    """Test that multiple curves maintain distinct colors."""
    curves_and_colors = [
        ("curve1", "#FF0000"),  # Red
        ("curve2", "#00FF00"),  # Green
        ("curve3", "#0000FF"),  # Blue
        ("curve4", None),       # No color, should get default
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

    # Verify colors
    assert rel_curves[0].pen.color == "#FF0000"
    assert rel_curves[1].pen.color == "#00FF00"
    assert rel_curves[2].pen.color == "#0000FF"
    assert rel_curves[3].pen.color == "#000000"  # Default black


def test_named_colors():
    """Test that named colors (not just hex) are preserved."""
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

    # Should preserve the named color
    assert rel_curve.pen.color == "red"


def test_pen_spec_validation():
    """Test that PenSpec accepts valid color values."""
    # Valid hex color
    pen1 = PenSpec(color="#ABCDEF")
    assert pen1.color == "#ABCDEF"

    # "none" for pen up
    pen2 = PenSpec(color="none")
    assert pen2.color == "none"

    # Named color
    pen3 = PenSpec(color="blue")
    assert pen3.color == "blue"


def test_color_override_precedence():
    """Test that curve color takes precedence over default."""
    curve = CurveDef(
        name="colored_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="#123456"
    )

    start_pose = (0.0, 0.0, 0.0)
    default_color = "#FEDCBA"

    rel_curve = wrap_to_relative(start_pose, curve, default_color=default_color)

    # Curve's explicit color should win
    assert rel_curve.pen.color == "#123456"
    assert rel_curve.pen.color != default_color


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

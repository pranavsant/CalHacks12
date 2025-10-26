"""
Test handling of degenerate derivatives (stationary points).

Verifies that curves with zero or near-zero velocity at endpoints
are handled gracefully without NaN or errors.
"""

import pytest
import math
import numpy as np
from backend.app.schemas import CurveDef
from backend.app.utils_relative import (
    compute_end_pose,
    wrap_to_relative,
    validate_relative_segment,
    compute_derivative_at_point
)


def test_stationary_endpoint_constant_curve():
    """Test a curve that ends at a stationary point (constant function)."""
    # Constant curve: x = 1, y = 1 (no velocity)
    curve = CurveDef(
        name="stationary",
        x="1",
        y="1",
        t_min=0.0,
        t_max=1.0,
        color="#FF0000"
    )

    pose = compute_end_pose(curve)

    # Position should be (1, 1)
    assert abs(pose[0] - 1.0) < 1e-6
    assert abs(pose[1] - 1.0) < 1e-6

    # Theta should default to 0 (not NaN)
    assert math.isfinite(pose[2])
    assert abs(pose[2] - 0.0) < 1e-6


def test_parabola_with_turning_point():
    """Test a parabola that has zero derivative at its vertex."""
    # Parabola with vertex at t=1: y = -(t-1)^2, x = t
    # At t=1, dy/dt = 0
    curve = CurveDef(
        name="parabola_vertex",
        x="t",
        y="-(t - 1)**2",
        t_min=0.0,
        t_max=1.0,  # End at the vertex
        color="#00FF00"
    )

    pose = compute_end_pose(curve)

    # Position at t=1: x=1, y=0
    assert abs(pose[0] - 1.0) < 1e-6
    assert abs(pose[1] - 0.0) < 1e-6

    # At t=1, dx/dt = 1, dy/dt = 0, so theta = atan2(0, 1) = 0
    assert math.isfinite(pose[2])
    # Should be close to 0 (horizontal, pointing right)
    assert abs(pose[2] - 0.0) < 1e-3


def test_cusp_point():
    """Test a curve with a cusp (both derivatives zero)."""
    # A cusp at t=0: x = t^2, y = t^2
    # At t=0, both dx/dt and dy/dt are 0
    # Coming from t=-1, the curve approaches from lower-left (both x and y decreasing)
    curve = CurveDef(
        name="cusp",
        x="t**2",
        y="t**2",
        t_min=-1.0,
        t_max=0.0,  # End at the cusp
        color="#0000FF"
    )

    pose = compute_end_pose(curve)

    # Position at t=0: x=0, y=0
    assert abs(pose[0] - 0.0) < 1e-6
    assert abs(pose[1] - 0.0) < 1e-6

    # Theta should be finite (finite difference picks up approach direction)
    # Coming from t < 0: dx/dt = 2t (negative), dy/dt = 2t (negative)
    # So theta ≈ atan2(-1, -1) ≈ -3π/4 ≈ -2.356 radians
    assert math.isfinite(pose[2])
    # Just verify it's finite, not NaN - the exact value depends on the approach direction


def test_very_slow_endpoint():
    """Test a curve that slows down to near-zero velocity at endpoint."""
    # Curve with exponential decay: x = 1 - exp(-5*t), y = 0
    # As t increases, dx/dt approaches 0
    curve = CurveDef(
        name="slow_end",
        x="1 - exp(-5*t)",
        y="0",
        t_min=0.0,
        t_max=5.0,  # Very slow at the end
        color="#FFFF00"
    )

    pose = compute_end_pose(curve)

    # Position should be finite
    assert math.isfinite(pose[0])
    assert math.isfinite(pose[1])

    # Theta should be finite (should default if derivative too small)
    assert math.isfinite(pose[2])


def test_derivative_computation_at_stationary_point():
    """Test that derivative computation handles stationary points."""
    # Constant expression
    expr = "5"
    derivative = compute_derivative_at_point(expr, 1.0)

    # Should be 0 or very close to 0
    assert abs(derivative) < 1e-6


def test_wrap_relative_with_degenerate_curve():
    """Test that wrap_to_relative handles degenerate derivatives gracefully."""
    # Create a stationary curve
    curve = CurveDef(
        name="stationary",
        x="2",
        y="3",
        t_min=0.0,
        t_max=1.0,
        color="#FF00FF"
    )

    # Previous pose with some rotation
    prev_pose = (1.0, 1.0, math.pi / 4)

    # This should not raise an error despite zero derivatives
    rel_curve = wrap_to_relative(prev_pose, curve)

    # Should validate successfully
    assert validate_relative_segment(rel_curve)

    # Expressions should be finite strings (no NaN in the constants)
    assert "nan" not in rel_curve.x_rel.lower()
    assert "nan" not in rel_curve.y_rel.lower()
    assert "inf" not in rel_curve.x_rel.lower()
    assert "inf" not in rel_curve.y_rel.lower()


def test_sequence_with_stationary_middle_segment():
    """Test a sequence of curves where the middle one is stationary."""
    # Segment 1: moving right
    seg1 = CurveDef(name="seg1", x="t", y="0", t_min=0, t_max=1, color="#FF0000")

    # Segment 2: stationary (represents a pause or marker)
    seg2 = CurveDef(name="seg2", x="1", y="0", t_min=0, t_max=1, color="#00FF00")

    # Segment 3: moving up
    seg3 = CurveDef(name="seg3", x="1", y="t", t_min=0, t_max=1, color="#0000FF")

    # Process all three
    pose = (0.0, 0.0, 0.0)
    curves = [seg1, seg2, seg3]

    for curve in curves:
        rel_curve = wrap_to_relative(pose, curve)

        # Should validate
        assert validate_relative_segment(rel_curve)

        # Update pose
        pose = compute_end_pose(curve)

        # Pose should always be finite
        assert all(math.isfinite(p) for p in pose)


def test_circular_arc_ending_at_horizontal():
    """Test a circular arc that ends at a point with horizontal tangent."""
    # Quarter circle: x = cos(t), y = sin(t), t from 0 to pi/2
    # At t=pi/2: x=0, y=1, dx/dt=-1, dy/dt=0, so theta = atan2(0, -1) = pi
    curve = CurveDef(
        name="quarter_circle",
        x="cos(t)",
        y="sin(t)",
        t_min=0.0,
        t_max=math.pi / 2,
        color="#00FFFF"
    )

    pose = compute_end_pose(curve)

    # Position at t=pi/2
    assert abs(pose[0] - 0.0) < 1e-6
    assert abs(pose[1] - 1.0) < 1e-6

    # Theta should be pi (pointing left) since dx/dt = -sin(pi/2) = -1, dy/dt = cos(pi/2) = 0
    assert math.isfinite(pose[2])
    assert abs(pose[2] - math.pi) < 1e-3


def test_zero_length_domain_is_invalid():
    """Test that curves with zero-length domains are caught as invalid."""
    curve = CurveDef(
        name="zero_length",
        x="t",
        y="t",
        t_min=1.0,
        t_max=1.0,  # Same as t_min
        color="#000000"
    )

    # Transform to relative
    rel_curve = wrap_to_relative((0, 0, 0), curve)

    # Should be flagged as invalid
    assert not validate_relative_segment(rel_curve)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

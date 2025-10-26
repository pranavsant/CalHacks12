"""
Test relative curve chaining correctness.

Verifies that transforming absolute curves to relative and then reconstructing
global positions yields the same result as the original absolute curves.
"""

import pytest
import math
import numpy as np
from backend.schemas import CurveDef, PenSpec
from backend.utils_relative import (
    compute_end_pose,
    wrap_to_relative,
    reconstruct_global_points,
    validate_relative_segment
)
from backend.renderer_agent import safe_eval_expression


def test_single_curve_identity():
    """Test that a single curve starting at origin transforms correctly."""
    # Create a simple horizontal line
    curve = CurveDef(
        name="horizontal_line",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="#FF0000"
    )

    # Transform to relative (starting from origin)
    start_pose = (0.0, 0.0, 0.0)
    relative_curve = wrap_to_relative(start_pose, curve)

    # Validate
    assert validate_relative_segment(relative_curve)

    # Reconstruct global points
    x_global, y_global = reconstruct_global_points(relative_curve, start_pose, num_points=100)

    # Sample original curve
    t_values = np.linspace(0.0, 1.0, 100)
    x_original = [safe_eval_expression(curve.x, t) for t in t_values]
    y_original = [safe_eval_expression(curve.y, t) for t in t_values]

    # Compare (should be identical within tolerance)
    np.testing.assert_allclose(x_global, x_original, atol=1e-3)
    np.testing.assert_allclose(y_global, y_original, atol=1e-3)


def test_two_connected_curves():
    """Test chaining two curves: horizontal line then quarter circle."""
    # Curve 1: Horizontal line from (0,0) to (1,0)
    curve1 = CurveDef(
        name="horizontal",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0,
        color="#FF0000"
    )

    # Curve 2: Quarter circle (starting at (1, 0), ending at (1, 1))
    # Absolute form: x = 1 + cos(t), y = sin(t) for t in [0, pi/2]
    # But we want it to start at (1, 0), so: x = 1, y = t for simplicity
    # Actually, let's use a proper quarter circle:
    # x = 1 - sin(t), y = 1 - cos(t) for t in [0, pi/2]
    # At t=0: x=1, y=0; at t=pi/2: x=1, y=1
    curve2 = CurveDef(
        name="quarter_circle",
        x="1 - sin(t)",
        y="1 - cos(t)",
        t_min=0.0,
        t_max=math.pi / 2,
        color="#00FF00"
    )

    # Transform both curves to relative
    # First curve starts at origin
    pose0 = (0.0, 0.0, 0.0)
    rel_curve1 = wrap_to_relative(pose0, curve1)

    # Get end pose of first curve
    pose1 = compute_end_pose(curve1)
    # Should be approximately (1.0, 0.0, 0.0) since it's a horizontal line to the right
    assert abs(pose1[0] - 1.0) < 1e-6
    assert abs(pose1[1] - 0.0) < 1e-6
    # theta should be 0 (pointing right)
    assert abs(pose1[2] - 0.0) < 1e-3

    # Transform second curve relative to end of first
    rel_curve2 = wrap_to_relative(pose1, curve2)

    # Validate both
    assert validate_relative_segment(rel_curve1)
    assert validate_relative_segment(rel_curve2)

    # Reconstruct global points for both
    x_global1, y_global1 = reconstruct_global_points(rel_curve1, pose0, num_points=50)
    x_global2, y_global2 = reconstruct_global_points(rel_curve2, pose1, num_points=50)

    # Sample original curves
    t1_values = np.linspace(0.0, 1.0, 50)
    x_orig1 = [safe_eval_expression(curve1.x, t) for t in t1_values]
    y_orig1 = [safe_eval_expression(curve1.y, t) for t in t1_values]

    t2_values = np.linspace(0.0, math.pi / 2, 50)
    x_orig2 = [safe_eval_expression(curve2.x, t) for t in t2_values]
    y_orig2 = [safe_eval_expression(curve2.y, t) for t in t2_values]

    # Compare first curve
    np.testing.assert_allclose(x_global1, x_orig1, atol=1e-3)
    np.testing.assert_allclose(y_global1, y_orig1, atol=1e-3)

    # Compare second curve
    np.testing.assert_allclose(x_global2, x_orig2, atol=1e-3)
    np.testing.assert_allclose(y_global2, y_orig2, atol=1e-3)


def test_circle_closed_loop():
    """Test a complete circle as a single curve."""
    # Circle centered at (1, 1) with radius 1
    curve = CurveDef(
        name="circle",
        x="1 + cos(t)",
        y="1 + sin(t)",
        t_min=0.0,
        t_max=2 * math.pi,
        color="#0000FF"
    )

    start_pose = (0.0, 0.0, 0.0)
    rel_curve = wrap_to_relative(start_pose, curve)

    assert validate_relative_segment(rel_curve)

    # Reconstruct
    x_global, y_global = reconstruct_global_points(rel_curve, start_pose, num_points=200)

    # Sample original
    t_values = np.linspace(0.0, 2 * math.pi, 200)
    x_orig = [safe_eval_expression(curve.x, t) for t in t_values]
    y_orig = [safe_eval_expression(curve.y, t) for t in t_values]

    # Compare
    np.testing.assert_allclose(x_global, x_orig, atol=1e-3)
    np.testing.assert_allclose(y_global, y_orig, atol=1e-3)

    # Check that end pose is close to start (should loop back)
    end_pose = compute_end_pose(curve)
    # Position should be back to (2, 1) - the start of the circle at t=0
    # x(0) = 1 + cos(0) = 2, y(0) = 1 + sin(0) = 1
    # x(2pi) = 1 + cos(2pi) = 2, y(2pi) = 1 + sin(2pi) = 1
    assert abs(end_pose[0] - 2.0) < 1e-3
    assert abs(end_pose[1] - 1.0) < 1e-3


def test_three_segment_path():
    """Test a path with three connected segments forming a smooth curve."""
    # Segment 1: horizontal line from (0, 0) to (1, 0)
    seg1 = CurveDef(name="seg1", x="t", y="0", t_min=0, t_max=1, color="#FF0000")

    # Segment 2: diagonal line from (1, 0) to (2, 1)
    seg2 = CurveDef(name="seg2", x="1 + t", y="t", t_min=0, t_max=1, color="#00FF00")

    # Segment 3: another horizontal from (2, 1) to (3, 1)
    seg3 = CurveDef(name="seg3", x="2 + t", y="1", t_min=0, t_max=1, color="#0000FF")

    curves = [seg1, seg2, seg3]
    poses = [(0.0, 0.0, 0.0)]

    rel_curves = []
    for i, curve in enumerate(curves):
        rel_curve = wrap_to_relative(poses[-1], curve)
        assert validate_relative_segment(rel_curve)
        rel_curves.append(rel_curve)

        # Compute next pose
        end_pose = compute_end_pose(curve)
        poses.append(end_pose)

    # Verify all segments are valid
    assert len(rel_curves) == 3

    # Test first segment reconstruction (should be identity since start pose is origin)
    x_global, y_global = reconstruct_global_points(rel_curves[0], poses[0], num_points=50)
    t_values = np.linspace(curves[0].t_min, curves[0].t_max, 50)
    x_orig = [safe_eval_expression(curves[0].x, t) for t in t_values]
    y_orig = [safe_eval_expression(curves[0].y, t) for t in t_values]

    np.testing.assert_allclose(x_global, x_orig, atol=1e-3,
                                err_msg="Segment 0 x coordinates don't match")
    np.testing.assert_allclose(y_global, y_orig, atol=1e-3,
                                err_msg="Segment 0 y coordinates don't match")


def test_end_pose_computation():
    """Test end pose computation for various curves."""
    # Horizontal line to the right
    curve = CurveDef(name="right", x="t", y="0", t_min=0, t_max=1, color="#000000")
    pose = compute_end_pose(curve)
    assert abs(pose[0] - 1.0) < 1e-6  # x = 1
    assert abs(pose[1] - 0.0) < 1e-6  # y = 0
    assert abs(pose[2] - 0.0) < 1e-3  # theta = 0 (pointing right)

    # Vertical line upward
    curve = CurveDef(name="up", x="0", y="t", t_min=0, t_max=1, color="#000000")
    pose = compute_end_pose(curve)
    assert abs(pose[0] - 0.0) < 1e-6  # x = 0
    assert abs(pose[1] - 1.0) < 1e-6  # y = 1
    assert abs(pose[2] - math.pi / 2) < 1e-3  # theta = pi/2 (pointing up)

    # Diagonal line (45 degrees)
    curve = CurveDef(name="diag", x="t", y="t", t_min=0, t_max=1, color="#000000")
    pose = compute_end_pose(curve)
    assert abs(pose[0] - 1.0) < 1e-6  # x = 1
    assert abs(pose[1] - 1.0) < 1e-6  # y = 1
    assert abs(pose[2] - math.pi / 4) < 1e-3  # theta = pi/4 (45 degrees)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Utilities for converting absolute parametric curves to relative local-frame representations.

This module provides functions to compute end poses of curves and transform curves
into relative coordinate frames for robot execution.
"""

import math
import logging
import numpy as np
from typing import Tuple, Optional
from .schemas import CurveDef, RelativeCurveDef, PenSpec
from .renderer_agent import safe_eval_expression

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_derivative_at_point(expr: str, t_value: float, delta: float = 1e-6) -> float:
    """
    Compute the derivative of an expression at a given t value using finite differences.

    Args:
        expr: Mathematical expression string
        t_value: Value of parameter t at which to compute derivative
        delta: Small step size for finite difference (default: 1e-6)

    Returns:
        The approximate derivative at t_value
    """
    try:
        # Use backward difference at the endpoint
        f_t = safe_eval_expression(expr, t_value)
        f_t_minus = safe_eval_expression(expr, t_value - delta)
        derivative = (f_t - f_t_minus) / delta
        return derivative
    except Exception as e:
        logger.warning(f"Error computing derivative for '{expr}' at t={t_value}: {e}")
        return 0.0


def compute_end_pose(curve: CurveDef) -> Tuple[float, float, float]:
    """
    Compute the pose (x, y, theta) at the end of a parametric curve.

    Args:
        curve: A CurveDef with x(t), y(t) expressions and t_min, t_max

    Returns:
        Tuple of (x_end, y_end, theta_end) where:
        - x_end = x(t_max)
        - y_end = y(t_max)
        - theta_end = atan2(y'(t_max), x'(t_max))

    If the derivative is degenerate (both x' and y' near zero),
    theta_end defaults to 0.0 to avoid NaN.
    """
    try:
        t_max = curve.t_max
        t_min = curve.t_min

        # Evaluate position at t_max
        x_end = safe_eval_expression(curve.x, t_max)
        y_end = safe_eval_expression(curve.y, t_max)

        # Compute derivatives at t_max using finite differences
        # Use a delta proportional to the t range
        delta = max(1e-6, 1e-3 * abs(t_max - t_min))
        delta = min(delta, abs(t_max - t_min) / 2.0)  # Don't exceed half the range

        x_prime = compute_derivative_at_point(curve.x, t_max, delta)
        y_prime = compute_derivative_at_point(curve.y, t_max, delta)

        # Check for degenerate case (stationary point)
        speed = math.sqrt(x_prime**2 + y_prime**2)
        if speed < 1e-9:
            logger.warning(
                f"Degenerate derivative for curve '{curve.name}' at t_max={t_max}. "
                f"Defaulting theta_end to 0.0"
            )
            theta_end = 0.0
        else:
            theta_end = math.atan2(y_prime, x_prime)

        logger.info(
            f"End pose for '{curve.name}': ({x_end:.6f}, {y_end:.6f}, {theta_end:.6f} rad)"
        )

        return (x_end, y_end, theta_end)

    except Exception as e:
        logger.error(f"Error computing end pose for curve '{curve.name}': {e}")
        # Return a safe default
        return (0.0, 0.0, 0.0)


def wrap_to_relative(
    prev_pose: Tuple[float, float, float],
    curve: CurveDef,
    default_color: Optional[str] = None
) -> RelativeCurveDef:
    """
    Transform an absolute parametric curve into a relative coordinate frame.

    The relative frame is defined by the previous segment's end pose.
    The transformation applies:
    1. Translation by -(x_end_prev, y_end_prev)
    2. Rotation by -theta_end_prev

    Args:
        prev_pose: The (x, y, theta) pose at the end of the previous segment
        curve: The absolute curve definition to transform
        default_color: Default pen color if curve has none; "none" means pen up

    Returns:
        A RelativeCurveDef with x_rel(t) and y_rel(t) expressions as strings.

    The returned expressions are of the form:
        x_rel(t) =  cos(A) * ( (x_orig(t)) - x_end_prev ) + sin(A) * ( (y_orig(t)) - y_end_prev )
        y_rel(t) = -sin(A) * ( (x_orig(t)) - x_end_prev ) + cos(A) * ( (y_orig(t)) - y_end_prev )
    where A = -theta_end_prev (embedded as a numeric constant).
    """
    try:
        x_prev, y_prev, theta_prev = prev_pose

        # Rotation angle is negative of previous theta
        angle = -theta_prev

        # Compute trig constants with high precision
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Format numeric constants with sufficient precision
        x_prev_str = f"{x_prev:.8f}"
        y_prev_str = f"{y_prev:.8f}"
        cos_a_str = f"{cos_a:.8f}"
        sin_a_str = f"{sin_a:.8f}"

        # Build relative expressions as strings
        # x_rel(t) = cos(A) * ( x(t) - x_prev ) + sin(A) * ( y(t) - y_prev )
        x_rel_expr = (
            f"{cos_a_str} * ( ({curve.x}) - {x_prev_str} ) + "
            f"{sin_a_str} * ( ({curve.y}) - {y_prev_str} )"
        )

        # y_rel(t) = -sin(A) * ( x(t) - x_prev ) + cos(A) * ( y(t) - y_prev )
        y_rel_expr = (
            f"{-sin_a:.8f} * ( ({curve.x}) - {x_prev_str} ) + "
            f"{cos_a_str} * ( ({curve.y}) - {y_prev_str} )"
        )

        # Determine pen color
        if curve.color:
            pen_color = curve.color
        elif default_color:
            pen_color = default_color
        else:
            # Default to black for drawing, unless explicitly "none"
            pen_color = "#000000"

        pen_spec = PenSpec(color=pen_color)

        relative_curve = RelativeCurveDef(
            name=curve.name,
            x_rel=x_rel_expr,
            y_rel=y_rel_expr,
            t_min=curve.t_min,
            t_max=curve.t_max,
            pen=pen_spec
        )

        logger.info(
            f"Transformed '{curve.name}' to relative frame from pose "
            f"({x_prev:.4f}, {y_prev:.4f}, {theta_prev:.4f})"
        )

        return relative_curve

    except Exception as e:
        logger.error(f"Error transforming curve '{curve.name}' to relative: {e}")
        raise


def validate_relative_segment(segment: RelativeCurveDef) -> bool:
    """
    Validate a relative curve segment for sanity.

    Checks:
    - t_min < t_max
    - Finite values
    - Non-zero length domain

    Args:
        segment: The relative curve segment to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        if not (segment.t_min < segment.t_max):
            logger.error(
                f"Invalid t range for segment '{segment.name}': "
                f"t_min={segment.t_min} >= t_max={segment.t_max}"
            )
            return False

        if not (math.isfinite(segment.t_min) and math.isfinite(segment.t_max)):
            logger.error(f"Non-finite t values in segment '{segment.name}'")
            return False

        # Check that domain has reasonable length
        if abs(segment.t_max - segment.t_min) < 1e-9:
            logger.error(
                f"Zero-length t domain for segment '{segment.name}': "
                f"{segment.t_min} to {segment.t_max}"
            )
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating segment '{segment.name}': {e}")
        return False


def reconstruct_global_points(
    relative_segment: RelativeCurveDef,
    start_pose: Tuple[float, float, float],
    num_points: int = 100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct global (x, y) points from a relative segment and a starting pose.

    This is useful for visualization and validation.

    Args:
        relative_segment: The relative curve segment
        start_pose: The (x, y, theta) pose to start from
        num_points: Number of points to sample

    Returns:
        Tuple of (x_global, y_global) as numpy arrays

    The forward transformation applies:
    1. Evaluate (x_rel(t), y_rel(t)) in local frame
    2. Rotate by theta_start
    3. Translate by (x_start, y_start)
    """
    try:
        x_start, y_start, theta_start = start_pose

        # Sample t values
        t_values = np.linspace(relative_segment.t_min, relative_segment.t_max, num_points)

        x_global = []
        y_global = []

        cos_theta = math.cos(theta_start)
        sin_theta = math.sin(theta_start)

        for t in t_values:
            # Evaluate in local frame
            x_local = safe_eval_expression(relative_segment.x_rel, t)
            y_local = safe_eval_expression(relative_segment.y_rel, t)

            # Transform to global frame
            # Rotate by theta_start
            x_rotated = cos_theta * x_local - sin_theta * y_local
            y_rotated = sin_theta * x_local + cos_theta * y_local

            # Translate by start position
            x_g = x_rotated + x_start
            y_g = y_rotated + y_start

            if math.isfinite(x_g) and math.isfinite(y_g):
                x_global.append(x_g)
                y_global.append(y_g)
            else:
                x_global.append(np.nan)
                y_global.append(np.nan)

        return np.array(x_global), np.array(y_global)

    except Exception as e:
        logger.error(f"Error reconstructing global points for '{relative_segment.name}': {e}")
        return np.array([]), np.array([])

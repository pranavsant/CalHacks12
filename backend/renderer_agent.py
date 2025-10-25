"""
Renderer Agent - Plots parametric curves using matplotlib.
This module takes parametric equations and generates visual images.
"""

import os
import math
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Static directory for saving images
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def safe_eval_expression(expr: str, t_value: float) -> float:
    """
    Safely evaluate a mathematical expression with parameter t.

    Args:
        expr: Mathematical expression string
        t_value: Value of parameter t

    Returns:
        The evaluated result
    """
    # Create a safe context with only math functions and the variable t
    safe_dict = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'exp': math.exp,
        'abs': abs,
        'log': math.log,
        'pi': math.pi,
        'e': math.e,
        't': t_value,
        '__builtins__': None
    }

    try:
        result = eval(expr, {"__builtins__": None}, safe_dict)
        return float(result)
    except Exception as e:
        logger.error(f"Error evaluating expression '{expr}' at t={t_value}: {e}")
        raise ValueError(f"Invalid expression: {expr}")


def plot_curve(ax: plt.Axes, curve: Dict[str, Any], num_points: int = 1000) -> None:
    """
    Plot a single parametric curve on the given axes.

    Args:
        ax: Matplotlib axes object
        curve: Curve definition with x, y, t_min, t_max, color
        num_points: Number of points to sample for smooth curve
    """
    try:
        # Extract curve parameters
        x_expr = curve['x']
        y_expr = curve['y']
        t_min = float(curve['t_min'])
        t_max = float(curve['t_max'])
        color = curve.get('color', '#4169E1')  # Default to royal blue
        name = curve.get('name', 'curve')

        logger.info(f"Plotting curve '{name}': x={x_expr}, y={y_expr}, t=[{t_min}, {t_max}]")

        # Generate t values
        t_values = np.linspace(t_min, t_max, num_points)

        # Evaluate x(t) and y(t) for each t
        x_values = []
        y_values = []

        for t in t_values:
            try:
                x = safe_eval_expression(x_expr, t)
                y = safe_eval_expression(y_expr, t)

                # Check for valid values (not NaN or infinite)
                if math.isfinite(x) and math.isfinite(y):
                    x_values.append(x)
                    y_values.append(y)
                else:
                    # Skip invalid points but don't break the curve
                    x_values.append(np.nan)
                    y_values.append(np.nan)
            except Exception as e:
                # Skip problematic points
                x_values.append(np.nan)
                y_values.append(np.nan)

        # Plot the curve
        ax.plot(x_values, y_values, color=color, linewidth=2, label=name)

        logger.info(f"Successfully plotted curve '{name}' with {len(x_values)} points")

    except KeyError as e:
        logger.error(f"Missing required field in curve definition: {e}")
        raise
    except Exception as e:
        logger.error(f"Error plotting curve: {e}")
        raise


def render_curves(curves_dict: Dict[str, Any], output_filename: str = None) -> str:
    """
    Render all curves to an image file.

    Args:
        curves_dict: Dictionary containing a 'curves' list
        output_filename: Optional custom filename (without extension)

    Returns:
        Path to the saved image file
    """
    logger.info(f"Rendering {len(curves_dict.get('curves', []))} curves")

    # Ensure static directory exists
    os.makedirs(STATIC_DIR, exist_ok=True)

    # Generate unique filename if not provided
    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        output_filename = f"output_{timestamp}_{unique_id}"

    output_path = os.path.join(STATIC_DIR, f"{output_filename}.png")

    try:
        # Create figure with high DPI for quality
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)

        # Set equal aspect ratio to avoid distortion
        ax.set_aspect('equal', adjustable='box')

        # Plot each curve
        curves = curves_dict.get('curves', [])
        if not curves:
            logger.warning("No curves to render")
            raise ValueError("No curves provided")

        for i, curve in enumerate(curves):
            try:
                plot_curve(ax, curve)
            except Exception as e:
                logger.error(f"Failed to plot curve {i}: {e}")
                # Continue with other curves

        # Configure the plot appearance
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.set_title('Parametric Curve Drawing', fontsize=14, fontweight='bold')

        # Add legend if there are multiple curves
        if len(curves) > 1:
            ax.legend(loc='best', fontsize=10, framealpha=0.9)

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save the figure
        plt.savefig(output_path, bbox_inches='tight', dpi=100, facecolor='white')
        plt.close(fig)

        logger.info(f"Successfully saved image to {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error in render_curves: {e}")
        # Clean up
        plt.close('all')
        raise


def get_image_as_base64(image_path: str) -> str:
    """
    Convert an image file to base64 data URL.

    Args:
        image_path: Path to the image file

    Returns:
        Base64-encoded data URL string
    """
    import base64

    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_data}"

        logger.info(f"Converted image to base64 ({len(base64_data)} characters)")
        return data_url

    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        raise


if __name__ == "__main__":
    # Test the renderer with a simple circle
    test_curves = {
        "curves": [
            {
                "name": "circle",
                "x": "cos(t)",
                "y": "sin(t)",
                "t_min": 0,
                "t_max": 2 * math.pi,
                "color": "#FF4500"
            }
        ]
    }

    output_path = render_curves(test_curves)
    print(f"Test image saved to: {output_path}")

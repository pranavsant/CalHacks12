#!/usr/bin/env python3
"""
Test script for robot_plotter in simulation mode.

This script creates a simple test program and runs it through the plotter
in simulation mode to verify the control logic without hardware.
"""

import json
import math
import tempfile
from robot_plotter import (
    execute_drawing_program,
    MotorController,
    PenController,
    DummyGPIO
)


def create_test_program():
    """Create a simple test program with a few basic shapes."""

    # Simple square path
    segments = []

    # Segment 1: Draw right edge (black)
    segments.append({
        "name": "right_edge",
        "x_rel": "1.00000000 * ((t) - 0.00000000) - 0.00000000 * ((0) - 0.00000000)",
        "y_rel": "0.00000000 * ((t) - 0.00000000) + 1.00000000 * ((0) - 0.00000000)",
        "t_min": 0.0,
        "t_max": 1.0,
        "pen": {"color": "#000000"}
    })

    # Segment 2: Draw top edge (black)
    segments.append({
        "name": "top_edge",
        "x_rel": "0.00000000 * ((1) - 1.00000000) - 1.00000000 * ((t) - 0.00000000)",
        "y_rel": "1.00000000 * ((1) - 1.00000000) + 0.00000000 * ((t) - 0.00000000)",
        "t_min": 0.0,
        "t_max": 1.0,
        "pen": {"color": "#000000"}
    })

    # Segment 3: Draw left edge (black)
    segments.append({
        "name": "left_edge",
        "x_rel": "-1.00000000 * ((1 - t) - 1.00000000) - 0.00000000 * ((1) - 1.00000000)",
        "y_rel": "0.00000000 * ((1 - t) - 1.00000000) + -1.00000000 * ((1) - 1.00000000)",
        "t_min": 0.0,
        "t_max": 1.0,
        "pen": {"color": "#000000"}
    })

    # Segment 4: Draw bottom edge (black)
    segments.append({
        "name": "bottom_edge",
        "x_rel": "0.00000000 * ((0) - 0.00000000) - -1.00000000 * ((1 - t) - 1.00000000)",
        "y_rel": "-1.00000000 * ((0) - 0.00000000) + 0.00000000 * ((1 - t) - 1.00000000)",
        "t_min": 0.0,
        "t_max": 1.0,
        "pen": {"color": "#000000"}
    })

    # Segment 5: Travel to circle center (pen up)
    segments.append({
        "name": "travel_to_circle",
        "x_rel": "1.00000000 * ((0.5) - 0.00000000) - 0.00000000 * ((0.5) - 0.00000000)",
        "y_rel": "0.00000000 * ((0.5) - 0.00000000) + 1.00000000 * ((0.5) - 0.00000000)",
        "t_min": 0.0,
        "t_max": 1.0,
        "pen": {"color": "none"}
    })

    # Segment 6: Draw circle (blue)
    segments.append({
        "name": "circle",
        "x_rel": "1.00000000 * ((0.3*cos(t) + 0.5) - 0.50000000) - 0.00000000 * ((0.3*sin(t) + 0.5) - 0.50000000)",
        "y_rel": "0.00000000 * ((0.3*cos(t) + 0.5) - 0.50000000) + 1.00000000 * ((0.3*sin(t) + 0.5) - 0.50000000)",
        "t_min": 0.0,
        "t_max": 2 * math.pi,
        "pen": {"color": "#0000FF"}
    })

    return {
        "run_id": "test_simulation",
        "prompt": "Test pattern: square with circle inside",
        "relative_program": {
            "segments": segments
        }
    }


def main():
    """Run simulation test."""
    print("="*70)
    print("ROBOT PLOTTER SIMULATION TEST")
    print("="*70)
    print()

    # Create test program
    print("Creating test program...")
    program = create_test_program()
    print(f"Program has {len(program['relative_program']['segments'])} segments")
    print()

    # Initialize controllers with dummy GPIO
    print("Initializing controllers (dummy GPIO)...")
    gpio = DummyGPIO()
    motor_controller = MotorController(gpio, simulate=True)
    pen_controller = PenController()
    print()

    try:
        # Execute the program
        print("Starting execution...")
        print()
        execute_drawing_program(
            motor_controller,
            pen_controller,
            program['relative_program']
        )

        print()
        print("="*70)
        print("✓ TEST COMPLETED SUCCESSFULLY")
        print("="*70)
        print()
        print("The simulation test completed without errors.")
        print("On real hardware, the robot would have drawn:")
        print("  1. A square (1 foot x 1 foot) in black")
        print("  2. A circle (0.6 foot diameter) inside the square in blue")
        print()

    except Exception as e:
        print()
        print("="*70)
        print("✗ TEST FAILED")
        print("="*70)
        print(f"Error: {e}")
        raise

    finally:
        # Cleanup
        pen_controller.cleanup()
        motor_controller.cleanup()


if __name__ == "__main__":
    main()

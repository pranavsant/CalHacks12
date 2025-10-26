#!/usr/bin/env python3
"""
Robot Plotter - Hardware Control Module for Differential Drive Drawing Robot

This script interfaces with the backend API to retrieve parametric drawing instructions
and drives a two-wheel differential robot with 28BYJ-48 stepper motors to trace curves.

Hardware Specifications:
- Track width (b): 0.02225 m (distance between wheel centers)
- Wheel radius (r): 0.0508 m
- Motors: 28BYJ-48 stepper motors (4096 half-steps per revolution)
- Left motor pins (BCM): [5, 6, 26, 21] (IN1-IN4)
- Right motor pins (BCM): [17, 27, 22, 16] (IN1-IN4)

Coordinate System:
- Drawing units: 1 unit = 1 foot = 0.3048 meters
- Robot starts at origin (0, 0) oriented along positive X-axis (0 radians)

Usage:
    python robot_plotter.py <run_id> [--backend-url URL] [--simulate]

    run_id: The unique identifier from /draw API response
    --backend-url: Backend API URL (default: http://localhost:8000)
    --simulate: Run in simulation mode without GPIO hardware
"""

import sys
import math
import time
import json
import logging
import argparse
from typing import Tuple, List, Dict, Optional

# Try to import RPi.GPIO, fall back to dummy implementation if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("RPi.GPIO not available - using dummy GPIO implementation")

# Try to import requests for API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: requests library not available. Install with: pip install requests")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DUMMY GPIO IMPLEMENTATION FOR TESTING/SIMULATION
# ============================================================================

class DummyGPIO:
    """Dummy GPIO implementation for testing without Raspberry Pi hardware."""

    BCM = "BCM"
    OUT = "OUT"
    LOW = 0
    HIGH = 1

    def __init__(self):
        self.mode = None
        self.pins = {}

    def setmode(self, mode):
        """Set pin numbering mode."""
        self.mode = mode
        logger.debug(f"[DUMMY GPIO] Set mode to {mode}")

    def setup(self, pin, direction):
        """Setup pin as input or output."""
        self.pins[pin] = {'direction': direction, 'state': self.LOW}
        logger.debug(f"[DUMMY GPIO] Setup pin {pin} as {direction}")

    def output(self, pin, state):
        """Set pin output state."""
        if pin in self.pins:
            self.pins[pin]['state'] = state
            # Uncomment for very verbose output:
            # logger.debug(f"[DUMMY GPIO] Pin {pin} -> {state}")

    def cleanup(self):
        """Clean up GPIO resources."""
        self.pins = {}
        logger.info("[DUMMY GPIO] Cleaned up all pins")


# ============================================================================
# HARDWARE CONSTANTS
# ============================================================================

# Physical dimensions
TRACK_WIDTH = 0.02225  # meters (distance between wheel centers)
WHEEL_RADIUS = 0.0508  # meters

# Unit conversion
FEET_TO_METERS = 0.3048  # 1 foot = 0.3048 meters

# Stepper motor specifications (28BYJ-48 in half-step mode)
STEPS_PER_REVOLUTION = 4096  # half-steps for full 360° rotation

# Calculate steps per meter of linear wheel travel
# Circumference = 2 * pi * r, so steps/meter = STEPS_PER_REVOLUTION / circumference
STEPS_PER_METER = STEPS_PER_REVOLUTION / (2 * math.pi * WHEEL_RADIUS)

# GPIO pin assignments (BCM numbering)
LEFT_MOTOR_PINS = [5, 6, 26, 21]   # IN1, IN2, IN3, IN4 for left motor
RIGHT_MOTOR_PINS = [17, 27, 22, 16]  # IN1, IN2, IN3, IN4 for right motor

# Half-step sequence for 28BYJ-48 stepper motor
# This gives 8 steps per cycle for maximum resolution
STEP_SEQUENCE = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
]

# Movement speed settings (seconds per step)
STEP_DELAY_DRAW = 0.002    # 2ms per step -> ~0.04 m/s drawing speed
STEP_DELAY_TRAVEL = 0.001  # 1ms per step -> ~0.08 m/s travel speed (pen up)

# Default backend URL
DEFAULT_BACKEND_URL = "http://localhost:8000"


# ============================================================================
# ROBOT STATE CLASS
# ============================================================================

class RobotState:
    """Maintains the current state of the robot (position, orientation, pen)."""

    def __init__(self):
        """Initialize robot at origin facing along positive X-axis."""
        self.x = 0.0  # meters
        self.y = 0.0  # meters
        self.theta = 0.0  # radians (0 = positive X-axis)
        self.pen_down = False
        self.current_color = None

    def update_position(self, dx: float, dy: float, dtheta: float):
        """Update robot position after a movement."""
        self.x += dx
        self.y += dy
        self.theta += dtheta
        # Normalize theta to [-pi, pi]
        while self.theta > math.pi:
            self.theta -= 2 * math.pi
        while self.theta < -math.pi:
            self.theta += 2 * math.pi

    def __str__(self):
        """String representation of current state."""
        return (f"Position: ({self.x:.4f}, {self.y:.4f}) m, "
                f"Heading: {math.degrees(self.theta):.2f}°, "
                f"Pen: {'DOWN' if self.pen_down else 'UP'}, "
                f"Color: {self.current_color}")


# ============================================================================
# MOTOR CONTROLLER CLASS
# ============================================================================

class MotorController:
    """Controls the stepper motors for the differential drive robot."""

    def __init__(self, gpio_module, simulate: bool = False):
        """
        Initialize motor controller.

        Args:
            gpio_module: GPIO module (either RPi.GPIO or DummyGPIO)
            simulate: If True, use dummy GPIO even if real GPIO is available
        """
        self.gpio = gpio_module
        self.simulate = simulate

        # Initialize GPIO
        self.gpio.setmode(self.gpio.BCM)

        # Setup motor pins as outputs
        for pin in LEFT_MOTOR_PINS + RIGHT_MOTOR_PINS:
            self.gpio.setup(pin, self.gpio.OUT)
            self.gpio.output(pin, self.gpio.LOW)

        # Current step indices for each motor (0-7 in the sequence)
        self.left_step_index = 0
        self.right_step_index = 0

        logger.info("Motor controller initialized")
        logger.info(f"Left motor pins: {LEFT_MOTOR_PINS}")
        logger.info(f"Right motor pins: {RIGHT_MOTOR_PINS}")

    def step_motor(self, motor: str, direction: int):
        """
        Perform one step on the specified motor.

        Args:
            motor: 'left' or 'right'
            direction: 1 for forward, -1 for backward
        """
        if motor == 'left':
            pins = LEFT_MOTOR_PINS
            self.left_step_index = (self.left_step_index + direction) % 8
            sequence_index = self.left_step_index
        elif motor == 'right':
            pins = RIGHT_MOTOR_PINS
            # Right motor is mounted in opposite orientation, so reverse direction
            self.right_step_index = (self.right_step_index - direction) % 8
            sequence_index = self.right_step_index
        else:
            raise ValueError(f"Invalid motor: {motor}")

        # Get the coil activation pattern for this step
        coil_pattern = STEP_SEQUENCE[sequence_index]

        # Activate the coils
        for pin, state in zip(pins, coil_pattern):
            self.gpio.output(pin, self.gpio.HIGH if state else self.gpio.LOW)

    def deenergize_motors(self):
        """Turn off all motor coils to save power and reduce heat."""
        for pin in LEFT_MOTOR_PINS + RIGHT_MOTOR_PINS:
            self.gpio.output(pin, self.gpio.LOW)
        logger.info("Motors de-energized")

    def cleanup(self):
        """Clean up GPIO resources."""
        self.deenergize_motors()
        self.gpio.cleanup()
        logger.info("Motor controller cleaned up")


# ============================================================================
# PEN CONTROLLER CLASS
# ============================================================================

class PenController:
    """Controls pen up/down and color changes (placeholder for future implementation)."""

    def __init__(self):
        """Initialize pen controller."""
        self.current_color = None
        self.is_down = False

    def pen_down(self, color: str):
        """
        Lower the pen with specified color.

        Args:
            color: Color code ("#000000" for black, "#0000FF" for blue, "none" for pen up)
        """
        if color == "none":
            logger.warning("pen_down called with color='none'")
            return

        if not self.is_down or self.current_color != color:
            logger.info(f"PEN DOWN - Color: {color}")

            # If changing colors, brief delay for pen change
            if self.is_down and self.current_color != color:
                logger.info(f"Changing pen from {self.current_color} to {color}")
                logger.info(">>> Please change the pen and press Enter to continue...")
                # In real implementation, could pause here: input()
                time.sleep(0.5)  # Small delay to simulate pen change

            self.current_color = color
            self.is_down = True

            # TODO: Implement actual servo control for pen mechanism
            # For example: set servo to "down" position
            # servo.set_angle(PEN_DOWN_ANGLE)
            time.sleep(0.3)  # Brief delay for pen to lower

    def pen_up(self):
        """Raise the pen."""
        if self.is_down:
            logger.info("PEN UP")
            self.is_down = False

            # TODO: Implement actual servo control for pen mechanism
            # For example: set servo to "up" position
            # servo.set_angle(PEN_UP_ANGLE)
            time.sleep(0.3)  # Brief delay for pen to raise

    def cleanup(self):
        """Clean up pen controller resources."""
        self.pen_up()


# ============================================================================
# PARAMETRIC PATH EVALUATOR
# ============================================================================

def safe_eval_expression(expr: str, t: float) -> float:
    """
    Safely evaluate a mathematical expression with parameter t.

    Args:
        expr: Mathematical expression string (e.g., "2*cos(t) + 3")
        t: Parameter value

    Returns:
        Evaluated result as float
    """
    # Create a restricted namespace with only safe math functions
    safe_namespace = {
        'cos': math.cos,
        'sin': math.sin,
        'tan': math.tan,
        'exp': math.exp,
        'log': math.log,
        'sqrt': math.sqrt,
        'abs': abs,
        'pi': math.pi,
        'e': math.e,
        't': t,
        '__builtins__': {}  # Restrict built-in functions
    }

    try:
        result = eval(expr, safe_namespace)
        return float(result)
    except Exception as e:
        logger.error(f"Error evaluating expression '{expr}' at t={t}: {e}")
        return 0.0


def sample_parametric_curve(x_expr: str, y_expr: str, t_min: float, t_max: float,
                           num_samples: int = 100) -> List[Tuple[float, float]]:
    """
    Sample a parametric curve at regular intervals.

    Args:
        x_expr: Expression for x(t)
        y_expr: Expression for y(t)
        t_min: Minimum parameter value
        t_max: Maximum parameter value
        num_samples: Number of sample points

    Returns:
        List of (x, y) coordinate tuples in meters
    """
    points = []

    for i in range(num_samples + 1):
        # Linear interpolation for t
        if num_samples > 0:
            t = t_min + (t_max - t_min) * (i / num_samples)
        else:
            t = t_min

        x = safe_eval_expression(x_expr, t) * FEET_TO_METERS
        y = safe_eval_expression(y_expr, t) * FEET_TO_METERS

        # Check for valid (finite) values
        if math.isfinite(x) and math.isfinite(y):
            points.append((x, y))
        else:
            logger.warning(f"Non-finite point at t={t}: ({x}, {y})")

    return points


# ============================================================================
# DIFFERENTIAL DRIVE KINEMATICS
# ============================================================================

def normalize_angle(angle: float) -> float:
    """
    Normalize angle to [-pi, pi] range.

    Args:
        angle: Angle in radians

    Returns:
        Normalized angle in [-pi, pi]
    """
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def compute_wheel_distances(distance: float, delta_theta: float) -> Tuple[float, float]:
    """
    Compute individual wheel distances for differential drive motion.

    Uses standard differential drive kinematics:
    - distance_left = d - (b/2) * Δθ
    - distance_right = d + (b/2) * Δθ

    Where:
    - d: linear distance traveled by robot center
    - Δθ: change in orientation (positive = counter-clockwise)
    - b: track width (distance between wheels)

    Args:
        distance: Linear distance for robot center to travel (meters)
        delta_theta: Change in orientation (radians)

    Returns:
        Tuple of (left_wheel_distance, right_wheel_distance) in meters
    """
    # Differential drive inverse kinematics
    distance_left = distance - (TRACK_WIDTH / 2.0) * delta_theta
    distance_right = distance + (TRACK_WIDTH / 2.0) * delta_theta

    return distance_left, distance_right


def compute_steps_for_motion(distance: float, delta_theta: float) -> Tuple[int, int]:
    """
    Convert motion (distance, angle change) to wheel step counts.

    Args:
        distance: Linear distance for robot center (meters)
        delta_theta: Change in orientation (radians)

    Returns:
        Tuple of (left_steps, right_steps) as integers
        Negative values indicate backward rotation
    """
    # Compute wheel distances
    distance_left, distance_right = compute_wheel_distances(distance, delta_theta)

    # Convert to steps
    left_steps = int(round(distance_left * STEPS_PER_METER))
    right_steps = int(round(distance_right * STEPS_PER_METER))

    logger.debug(f"Motion: d={distance:.4f}m, Δθ={math.degrees(delta_theta):.2f}°")
    logger.debug(f"Wheel distances: L={distance_left:.4f}m, R={distance_right:.4f}m")
    logger.debug(f"Steps: L={left_steps}, R={right_steps}")

    return left_steps, right_steps


# ============================================================================
# SYNCHRONIZED MOTOR STEPPING (BRESENHAM ALGORITHM)
# ============================================================================

def execute_synchronized_motion(motor_controller: MotorController,
                                left_steps: int, right_steps: int,
                                step_delay: float):
    """
    Execute synchronized motion of both motors using Bresenham's algorithm.

    This ensures both motors finish their steps at the same time, maintaining
    the correct path curvature. Uses integer-only Bresenham line algorithm
    to determine when each motor should step.

    Args:
        motor_controller: MotorController instance
        left_steps: Number of steps for left motor (can be negative)
        right_steps: Number of steps for right motor (can be negative)
        step_delay: Delay between steps in seconds
    """
    # Determine directions
    left_dir = 1 if left_steps >= 0 else -1
    right_dir = 1 if right_steps >= 0 else -1

    # Get absolute step counts
    left_count = abs(left_steps)
    right_count = abs(right_steps)

    # Handle trivial cases
    if left_count == 0 and right_count == 0:
        return  # No motion

    # Determine major axis (motor that steps most frequently)
    if left_count >= right_count:
        major_count = left_count
        minor_count = right_count
        major_motor = 'left'
        minor_motor = 'right'
        major_dir = left_dir
        minor_dir = right_dir
    else:
        major_count = right_count
        minor_count = left_count
        major_motor = 'right'
        minor_motor = 'left'
        major_dir = right_dir
        minor_dir = left_dir

    # Bresenham algorithm: accumulate error to determine when to step minor motor
    error = 0

    for i in range(major_count):
        # Always step the major motor
        motor_controller.step_motor(major_motor, major_dir)

        # Accumulate error and step minor motor when threshold exceeded
        error += minor_count
        if error >= major_count:
            motor_controller.step_motor(minor_motor, minor_dir)
            error -= major_count
        elif minor_count > 0 and i < minor_count:
            # For the case where minor motor also needs steps
            # This handles the remaining minor motor steps
            pass

        # Delay between steps
        time.sleep(step_delay)

    # Handle any remaining minor motor steps (shouldn't happen with proper Bresenham)
    # This is a safeguard for floating point rounding issues
    remaining_minor = minor_count - (major_count - error) // major_count
    if remaining_minor > 0:
        for _ in range(remaining_minor):
            motor_controller.step_motor(minor_motor, minor_dir)
            time.sleep(step_delay)


def execute_motion_segment(motor_controller: MotorController,
                           start_point: Tuple[float, float],
                           end_point: Tuple[float, float],
                           current_theta: float,
                           pen_down: bool) -> Tuple[float, float, float]:
    """
    Execute motion from start_point to end_point.

    Args:
        motor_controller: MotorController instance
        start_point: Starting (x, y) in meters
        end_point: Ending (x, y) in meters
        current_theta: Current robot orientation in radians
        pen_down: Whether pen is down (affects speed)

    Returns:
        Tuple of (dx, dy, new_theta) - the actual motion executed
    """
    # Compute movement vector
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]

    # Compute distance
    distance = math.sqrt(dx**2 + dy**2)

    if distance < 1e-6:
        # No significant movement
        return 0.0, 0.0, current_theta

    # Compute desired heading
    target_theta = math.atan2(dy, dx)

    # Compute required rotation
    delta_theta = normalize_angle(target_theta - current_theta)

    # Compute wheel steps
    left_steps, right_steps = compute_steps_for_motion(distance, delta_theta)

    # Choose step delay based on pen state
    step_delay = STEP_DELAY_DRAW if pen_down else STEP_DELAY_TRAVEL

    # Log the motion
    speed = 1.0 / (step_delay * STEPS_PER_METER) if step_delay > 0 else 0
    logger.info(f"Moving: d={distance*1000:.2f}mm, Δθ={math.degrees(delta_theta):.2f}°, "
                f"speed≈{speed:.3f}m/s, steps=({left_steps}, {right_steps})")

    # Execute synchronized motion
    execute_synchronized_motion(motor_controller, left_steps, right_steps, step_delay)

    # Return the executed motion
    new_theta = normalize_angle(current_theta + delta_theta)
    return dx, dy, new_theta


# ============================================================================
# PATH EXECUTION
# ============================================================================

def execute_segment(motor_controller: MotorController,
                   pen_controller: PenController,
                   robot_state: RobotState,
                   segment: Dict) -> None:
    """
    Execute a single relative curve segment.

    Args:
        motor_controller: MotorController instance
        pen_controller: PenController instance
        robot_state: Current robot state
        segment: Segment definition from API (relative curve)
    """
    segment_name = segment.get('name', 'unknown')
    x_rel_expr = segment['x_rel']
    y_rel_expr = segment['y_rel']
    t_min = segment['t_min']
    t_max = segment['t_max']
    pen_spec = segment['pen']
    color = pen_spec['color']

    logger.info(f"\n{'='*70}")
    logger.info(f"Executing segment: {segment_name}")
    logger.info(f"  Color: {color}")
    logger.info(f"  Parameter range: t ∈ [{t_min}, {t_max}]")
    logger.info(f"  Current state: {robot_state}")

    # Determine if this is a drawing or travel segment
    is_drawing = (color != "none")

    # Handle pen state
    if is_drawing:
        pen_controller.pen_down(color)
        robot_state.pen_down = True
        robot_state.current_color = color
    else:
        pen_controller.pen_up()
        robot_state.pen_down = False

    # Sample the parametric curve into discrete points
    # Use more samples for drawing (higher accuracy) vs travel
    num_samples = 100 if is_drawing else 50
    points = sample_parametric_curve(x_rel_expr, y_rel_expr, t_min, t_max, num_samples)

    if len(points) < 2:
        logger.warning(f"Segment {segment_name} has insufficient points, skipping")
        return

    logger.info(f"  Sampled {len(points)} points")

    # Execute motion through all points
    current_pos = (0.0, 0.0)  # In local frame, we always start at origin

    for i, point in enumerate(points[1:], 1):
        # Execute motion from current position to next point
        dx, dy, new_theta = execute_motion_segment(
            motor_controller,
            current_pos,
            point,
            robot_state.theta,
            robot_state.pen_down
        )

        # Update state
        robot_state.update_position(dx, dy, new_theta - robot_state.theta)
        current_pos = point

        # Periodic status update
        if i % 20 == 0:
            progress = (i / len(points)) * 100
            logger.info(f"  Progress: {progress:.1f}% - {robot_state}")

    logger.info(f"Segment complete: {segment_name}")


def execute_drawing_program(motor_controller: MotorController,
                           pen_controller: PenController,
                           program: Dict) -> None:
    """
    Execute the complete drawing program.

    Args:
        motor_controller: MotorController instance
        pen_controller: PenController instance
        program: Complete program from API (with 'segments' list)
    """
    segments = program['segments']
    total_segments = len(segments)

    logger.info(f"\n{'='*70}")
    logger.info(f"STARTING DRAWING PROGRAM")
    logger.info(f"Total segments: {total_segments}")
    logger.info(f"{'='*70}\n")

    # Initialize robot state
    robot_state = RobotState()

    try:
        # Execute each segment in sequence
        for i, segment in enumerate(segments, 1):
            logger.info(f"\n--- Segment {i}/{total_segments} ---")
            execute_segment(motor_controller, pen_controller, robot_state, segment)

        logger.info(f"\n{'='*70}")
        logger.info("DRAWING PROGRAM COMPLETE!")
        logger.info(f"Final state: {robot_state}")
        logger.info(f"{'='*70}\n")

    except KeyboardInterrupt:
        logger.warning("\n!!! Drawing interrupted by user !!!")
        raise
    finally:
        # Always ensure pen is up at the end
        pen_controller.pen_up()


# ============================================================================
# API CLIENT
# ============================================================================

def fetch_drawing_program(backend_url: str, run_id: str) -> Dict:
    """
    Fetch drawing program from backend API.

    Args:
        backend_url: Base URL of backend API
        run_id: Run identifier

    Returns:
        Drawing program dict with run_id, prompt, and relative_program

    Raises:
        RuntimeError: If fetch fails
    """
    if not REQUESTS_AVAILABLE:
        raise RuntimeError("requests library not available. Install with: pip install requests")

    url = f"{backend_url}/robot/{run_id}"
    logger.info(f"Fetching program from: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if 'relative_program' not in data:
            raise RuntimeError("Invalid response: missing 'relative_program'")

        if 'segments' not in data['relative_program']:
            raise RuntimeError("Invalid response: missing 'segments' in relative_program")

        logger.info(f"Successfully fetched program for run: {run_id}")
        logger.info(f"Prompt: {data.get('prompt', 'N/A')}")
        logger.info(f"Segments: {len(data['relative_program']['segments'])}")

        return data

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch program: {e}")


def load_program_from_file(file_path: str) -> Dict:
    """
    Load drawing program from local JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Drawing program dict

    Raises:
        RuntimeError: If load fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if 'relative_program' not in data:
            raise RuntimeError("Invalid file: missing 'relative_program'")

        logger.info(f"Successfully loaded program from: {file_path}")
        logger.info(f"Prompt: {data.get('prompt', 'N/A')}")
        logger.info(f"Segments: {len(data['relative_program']['segments'])}")

        return data

    except (IOError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load program file: {e}")


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """Main entry point for robot plotter."""
    parser = argparse.ArgumentParser(
        description="Robot Plotter - Drive differential robot to draw parametric curves",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch from backend and draw
  python robot_plotter.py 09eab5f54708495bb9c5e51b7d90ecbe

  # Use custom backend URL
  python robot_plotter.py <run_id> --backend-url http://192.168.1.100:8000

  # Simulate without hardware
  python robot_plotter.py <run_id> --simulate

  # Load from local file
  python robot_plotter.py --file backend/exports/relative_program_<run_id>.json --simulate
        """
    )

    parser.add_argument('run_id', nargs='?', help='Run ID from backend /draw API response')
    parser.add_argument('--backend-url', default=DEFAULT_BACKEND_URL,
                       help=f'Backend API URL (default: {DEFAULT_BACKEND_URL})')
    parser.add_argument('--simulate', action='store_true',
                       help='Run in simulation mode without GPIO hardware')
    parser.add_argument('--file', help='Load program from local JSON file instead of API')

    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.run_id:
        parser.error("Either run_id or --file must be specified")

    # Setup GPIO module
    if args.simulate or not GPIO_AVAILABLE:
        gpio_module = DummyGPIO()
        logger.info("Running in SIMULATION mode")
    else:
        gpio_module = GPIO
        logger.info("Running in HARDWARE mode with RPi.GPIO")

    # Initialize controllers
    motor_controller = None
    pen_controller = None

    try:
        # Load program
        if args.file:
            program_data = load_program_from_file(args.file)
        else:
            program_data = fetch_drawing_program(args.backend_url, args.run_id)

        # Initialize hardware controllers
        motor_controller = MotorController(gpio_module, simulate=args.simulate)
        pen_controller = PenController()

        # Execute the drawing
        execute_drawing_program(
            motor_controller,
            pen_controller,
            program_data['relative_program']
        )

        logger.info("\n✓ Drawing completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n!!! Program interrupted by user (Ctrl+C) !!!")
        return 1

    except Exception as e:
        logger.error(f"\n✗ Error: {e}", exc_info=True)
        return 1

    finally:
        # Always clean up hardware resources
        if pen_controller:
            try:
                pen_controller.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up pen controller: {e}")

        if motor_controller:
            try:
                motor_controller.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up motor controller: {e}")


if __name__ == "__main__":
    sys.exit(main())

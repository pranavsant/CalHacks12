# Robot Plotter Hardware Control Module

This directory contains the hardware control code for the differential drive drawing robot. The robot uses two 28BYJ-48 stepper motors to trace parametric curves retrieved from the backend API.

## Overview

The `robot_plotter.py` script:
- Fetches parametric drawing instructions from the backend API
- Converts relative curve segments into motor commands
- Controls two stepper motors via GPIO to trace out curves
- Handles pen up/down logic for color changes
- Uses accurate differential drive kinematics to prevent drift

## Hardware Specifications

### Physical Dimensions
- **Track Width (b)**: 0.02225 m (22.25 mm) - distance between wheel centers
- **Wheel Radius (r)**: 0.0508 m (50.8 mm)

### Motors
- **Type**: 28BYJ-48 stepper motors with ULN2003 drivers
- **Resolution**: 4096 half-steps per full revolution (5.625°/64 per step)
- **Control Mode**: Half-step for maximum resolution

### GPIO Pin Assignments (BCM Numbering)

**Left Motor** (IN1-IN4):
- BCM Pin 5 → IN1
- BCM Pin 6 → IN2
- BCM Pin 26 → IN3
- BCM Pin 21 → IN4

**Right Motor** (IN1-IN4):
- BCM Pin 17 → IN1
- BCM Pin 27 → IN2
- BCM Pin 22 → IN3
- BCM Pin 16 → IN4

### Movement Speeds
- **Drawing Speed** (pen down): ~0.04 m/s (2ms per step)
- **Travel Speed** (pen up): ~0.08 m/s (1ms per step)

## Installation

### On Raspberry Pi

1. **Install Python dependencies**:
   ```bash
   pip install requests RPi.GPIO
   ```

2. **Make the script executable** (optional):
   ```bash
   chmod +x hardware/robot_plotter.py
   ```

### On Development Machine (Simulation)

For testing without Raspberry Pi hardware:

```bash
pip install requests
```

The script will automatically use a dummy GPIO implementation when `RPi.GPIO` is not available.

## Usage

### Basic Usage

```bash
# Fetch and draw using run_id from backend
python hardware/robot_plotter.py <run_id>
```

### Advanced Options

```bash
# Use custom backend URL
python hardware/robot_plotter.py <run_id> --backend-url http://192.168.1.100:8000

# Simulate without hardware (for testing)
python hardware/robot_plotter.py <run_id> --simulate

# Load from local JSON file
python hardware/robot_plotter.py --file backend/exports/relative_program_<run_id>.json --simulate
```

### Getting a Run ID

1. Send a drawing request to the backend:
   ```bash
   curl -X POST http://localhost:8000/draw \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Draw a heart shape"}'
   ```

2. The response will include a `run_id` (hex UUID):
   ```json
   {
     "success": true,
     "run_id": "09eab5f54708495bb9c5e51b7d90ecbe",
     ...
   }
   ```

3. Use this `run_id` with the robot plotter:
   ```bash
   python hardware/robot_plotter.py 09eab5f54708495bb9c5e51b7d90ecbe
   ```

## Architecture

### Key Components

1. **MotorController**: Controls the two stepper motors
   - Manages GPIO pin states
   - Implements half-step sequences
   - Handles motor direction (accounting for opposite mounting)

2. **PenController**: Manages pen up/down and color changes
   - Currently logs actions (placeholder for servo control)
   - Handles color change prompts

3. **RobotState**: Tracks robot position and orientation
   - Current (x, y) position in meters
   - Heading angle θ in radians
   - Pen state and current color

4. **Differential Drive Kinematics**: Converts path to wheel motions
   - Computes required rotation for each path segment
   - Calculates individual wheel distances using inverse kinematics
   - Prevents drift through accurate math

5. **Bresenham Stepping**: Synchronizes both motors
   - Ensures both wheels finish simultaneously
   - Maintains correct path curvature
   - Integer-only algorithm for efficiency

### Coordinate Systems

**Backend Output** (from API):
- Units: 1 unit = 1 foot = 0.3048 meters
- Relative coordinates: each segment is in local frame of previous segment's endpoint

**Robot Frame**:
- Units: meters
- Origin: robot's starting position
- X-axis: initial forward direction
- Positive rotation: counter-clockwise (right-hand rule)

### Differential Drive Kinematics

The robot uses standard differential drive equations:

```
distance_left = d - (b/2) * Δθ
distance_right = d + (b/2) * Δθ
```

Where:
- `d`: linear distance traveled by robot center
- `Δθ`: change in orientation (radians)
- `b`: track width (0.02225 m)

For each path segment:
1. Compute desired heading from current position to target
2. Calculate required rotation Δθ
3. Compute wheel distances using equations above
4. Convert to motor steps: `steps = distance * (4096 / (2πr))`
5. Execute synchronized stepping using Bresenham algorithm

## Path Execution Flow

1. **Fetch Program**: Retrieve `relative_program` from backend API
2. **Initialize**: Set robot at origin (0,0) facing +X axis, pen up
3. **For Each Segment**:
   - Check color: if changed from previous, raise pen and prompt for pen change
   - Lower pen if drawing segment (color ≠ "none")
   - Sample parametric curve into discrete points
   - Execute motion through all points:
     - Compute Δx, Δy to next point
     - Calculate required heading change Δθ
     - Compute wheel steps from (d, Δθ)
     - Execute synchronized stepping at appropriate speed
     - Update robot state
4. **Cleanup**: Raise pen, de-energize motors, cleanup GPIO

## Color Handling

The backend provides three color values:
- `"#000000"`: Black pen (drawing)
- `"#0000FF"`: Blue pen (drawing)
- `"none"`: Pen up (travel, no drawing)

When a color change occurs:
1. Raise pen (if it was down)
2. Log color change (prompt for manual pen swap in future)
3. Lower pen with new color

**Future Implementation**: Add servo control for automated pen lift/lower and potentially automated pen changer mechanism.

## Mathematical Verification

The differential drive math has been verified against several test cases:

**Straight Line** (Δθ = 0):
- Both wheels travel equal distance: `d_left = d_right = d` ✓

**Pure Rotation** (d ≈ 0, Δθ ≠ 0):
- Wheels travel opposite directions: `d_left = -d_right = ±(b/2)Δθ` ✓
- Robot pivots about center ✓

**Gentle Curve** (small Δθ):
- Outer wheel travels slightly more than inner wheel ✓
- Ratio matches expected arc geometry ✓

**Sharp Turn**:
- Inner wheel may reverse if radius < b/2 ✓
- Kinematics handle negative steps correctly ✓

## Troubleshooting

### Robot Doesn't Move

1. **Check GPIO connections**:
   - Verify BCM pin numbers match your wiring
   - Test with LED or multimeter

2. **Check motor power**:
   - ULN2003 drivers need external 5V power supply
   - Verify power to motor coils

3. **Test individual motors**:
   - Add debug logging to see step commands
   - Manually test each motor independently

### Robot Moves Incorrectly

1. **Direction reversed**:
   - Check motor mounting orientation
   - Verify right motor reversal in code (line ~200)

2. **Drift or curves wrong**:
   - Verify `TRACK_WIDTH` and `WHEEL_RADIUS` constants
   - Measure your actual robot dimensions
   - Check wheel slip on surface

3. **Steps too fast/slow**:
   - Adjust `STEP_DELAY_DRAW` and `STEP_DELAY_TRAVEL`
   - Slower = more torque but slower drawing

### API Connection Issues

1. **Backend not reachable**:
   ```bash
   # Test backend is running
   curl http://localhost:8000/health
   ```

2. **Run ID not found**:
   - Check the `backend/exports/` directory for JSON files
   - Verify run_id matches filename (without `relative_program_` prefix and `.json` suffix)

3. **Use local file as fallback**:
   ```bash
   python hardware/robot_plotter.py --file backend/exports/relative_program_<run_id>.json --simulate
   ```

## Testing

### Simulation Mode

Test the entire control logic without hardware:

```bash
python hardware/robot_plotter.py <run_id> --simulate
```

This will:
- Use dummy GPIO (logs actions instead of controlling pins)
- Execute full path planning and kinematics
- Print detailed step-by-step execution log

### Unit Tests (Future)

Create test files to verify:
- Kinematics calculations
- Step count conversions
- Bresenham algorithm
- Path sampling accuracy

### Example Test

```python
# Test straight line motion
from robot_plotter import compute_steps_for_motion

# 0.1m forward, no rotation
left_steps, right_steps = compute_steps_for_motion(0.1, 0.0)
assert left_steps == right_steps  # Should be equal
assert abs(left_steps - 1283) < 5  # Approximately 1283 steps for 0.1m
```

## Safety Considerations

1. **Always supervise** the robot during operation
2. **Emergency stop**: Press Ctrl+C to interrupt (cleanup will still run)
3. **Workspace**: Ensure drawing surface is clear of obstacles
4. **Power**: Use proper power supply for motors (5V, sufficient amperage)
5. **GPIO cleanup**: Script automatically cleans up on exit

## Future Enhancements

1. **Servo Control**: Implement actual pen up/down mechanism
2. **Pen Changer**: Automated mechanism for swapping pen colors
3. **Homing**: Add limit switches or endstops for position calibration
4. **Acceleration**: Implement S-curve acceleration for smoother motion
5. **Error Recovery**: Handle motor stalls, position loss
6. **Real-time Visualization**: Web interface showing robot position during drawing
7. **Path Optimization**: Pre-process paths to reduce travel time
8. **Multiple Pen Carousel**: Automatic selection from multiple colors

## References

- [28BYJ-48 Stepper Motor Datasheet](https://www.electronicoscaldas.com/datasheet/28BYJ-48_Datasheet.pdf)
- [ULN2003 Driver IC Datasheet](https://www.ti.com/lit/ds/symlink/uln2003a.pdf)
- Differential Drive Kinematics: *Introduction to Autonomous Mobile Robots* (Siegwart & Nourbakhsh)
- Bresenham's Line Algorithm: [Wikipedia](https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend API documentation
3. Verify hardware connections and specifications
4. Test in simulation mode first

## License

This code is part of the CalHacks12 Parametric Drawing System project.

# Quick Start Guide - Robot Plotter

Get your robot drawing in 5 minutes!

## Prerequisites

- Raspberry Pi with Raspbian/Raspberry Pi OS
- Two 28BYJ-48 stepper motors with ULN2003 drivers
- Proper GPIO connections (see wiring diagram below)
- Backend API running (on Pi or accessible via network)

## Installation

### 1. Install Dependencies

```bash
pip install requests RPi.GPIO
```

### 2. Verify Backend is Running

```bash
# On the same machine as backend
curl http://localhost:8000/health

# Or from Pi to remote backend
curl http://<backend-ip>:8000/health
```

Expected response:
```json
{"status": "healthy", "services": {...}}
```

## Running Your First Drawing

### Step 1: Create a Drawing

Use the frontend or API to create a drawing:

```bash
# Example: Create a simple drawing via API
curl -X POST http://localhost:8000/draw \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Draw a simple heart shape"}'
```

Save the `run_id` from the response.

### Step 2: Run the Robot Plotter

```bash
cd CalHacks12/hardware
python robot_plotter.py <run_id>
```

Or with remote backend:

```bash
python robot_plotter.py <run_id> --backend-url http://192.168.1.100:8000
```

### Step 3: Watch It Draw!

The robot will:
1. Fetch the drawing program from the backend
2. Lower the pen and start drawing
3. Automatically lift pen for color changes
4. Complete the drawing and cleanup

## Testing Without Hardware

Test the complete control logic in simulation mode:

```bash
# Test with simulation
python robot_plotter.py <run_id> --simulate

# Or run the built-in test
python test_simulation.py
```

## Wiring Diagram

### Left Motor (ULN2003 Driver)
```
Raspberry Pi (BCM)    ULN2003 Driver
------------------    --------------
GPIO 5         -->    IN1
GPIO 6         -->    IN2
GPIO 26        -->    IN3
GPIO 21        -->    IN4

5V             -->    VCC (external power supply)
GND            -->    GND
```

### Right Motor (ULN2003 Driver)
```
Raspberry Pi (BCM)    ULN2003 Driver
------------------    --------------
GPIO 17        -->    IN1
GPIO 27        -->    IN2
GPIO 22        -->    IN3
GPIO 16        -->    IN4

5V             -->    VCC (external power supply)
GND            -->    GND
```

**IMPORTANT**:
- Use BCM pin numbering (not BOARD numbering)
- Connect motors to external 5V power supply (NOT the Pi's 5V pin)
- Common ground between Pi and motor power supply

## Troubleshooting

### Robot Doesn't Move

**Check connections:**
```bash
# Test GPIO with LED
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(5, GPIO.OUT); GPIO.output(5, GPIO.HIGH); import time; time.sleep(2); GPIO.cleanup()"
```

LED should light up on GPIO 5.

**Check power:**
- Verify 5V power supply is connected to motor drivers
- Ensure sufficient current capacity (>500mA per motor)

### Backend Connection Failed

```bash
# Test connectivity
ping <backend-ip>

# Test API
curl http://<backend-ip>:8000/health

# Check run_id exists
curl http://<backend-ip>:8000/robot/<run_id>
```

### Wrong Direction or Drift

1. **Measure your robot dimensions** (may differ from defaults)
2. **Update constants** in `robot_plotter.py`:
   ```python
   TRACK_WIDTH = 0.02225  # Your measured track width in meters
   WHEEL_RADIUS = 0.0508  # Your measured wheel radius in meters
   ```

## Common Commands

```bash
# Basic usage
python robot_plotter.py <run_id>

# Remote backend
python robot_plotter.py <run_id> --backend-url http://192.168.1.10:8000

# Simulation (no hardware)
python robot_plotter.py <run_id> --simulate

# Load from local file
python robot_plotter.py --file ../backend/exports/relative_program_<run_id>.json

# Test simulation
python test_simulation.py

# View help
python robot_plotter.py --help
```

## Example Workflow

```bash
# 1. Start backend (in another terminal or remote machine)
cd CalHacks12/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Create a drawing
curl -X POST http://localhost:8000/draw \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Draw a simple star"}' \
  | jq '.run_id'

# Output: "abc123def456..."

# 3. Run robot
cd CalHacks12/hardware
python robot_plotter.py abc123def456

# 4. Watch your robot draw a star!
```

## Safety Tips

- ✓ Always supervise the robot during operation
- ✓ Keep emergency stop ready (Ctrl+C)
- ✓ Ensure workspace is clear of obstacles
- ✓ Use proper power supply for motors (not Pi's 5V rail)
- ✓ Test in simulation mode first

## Next Steps

After your first successful drawing:

1. **Calibrate**: Fine-tune `TRACK_WIDTH` and `WHEEL_RADIUS` for accuracy
2. **Add Pen Control**: Implement servo for automatic pen up/down
3. **Optimize**: Adjust speeds in code for your surface/pen combination
4. **Create Complex Drawings**: Try more elaborate prompts

## Need Help?

- See full documentation: [README.md](README.md)
- Check backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Review hardware specs in main README
- Run simulation test to verify logic

Happy Drawing! 🎨🤖

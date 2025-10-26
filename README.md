# Parametric Curve Drawing System

Transform natural language (or voice) prompts into mathematical parametric curves and rendered images using AI.

## Overview

The Parametric Curve Drawing System is an automated pipeline that converts descriptive prompts like "Draw a butterfly" into mathematical parametric equations and visualizes them as images. Built for Cal Hacks 12.0, it integrates multiple AI technologies:

- **[Anthropic Claude Sonnet 4.5](https://anthropic.com)** - Natural language understanding and mathematical reasoning
- **[Vapi](https://vapi.ai)** - Voice-to-text transcription (optional)
- **[Letta Cloud](https://letta.com)** - Persistent memory across sessions (optional)
- **[Fetch.ai Agentverse](https://fetch.ai)** - Multi-agent orchestration framework (optional)
- **[Composio](https://composio.dev)** - Tool routing and MCP integration (future enhancement)

## Architecture

The system operates through five main phases:

1. **Input Processing** - Convert voice or text into structured descriptions
2. **Equation Generation** - Generate parametric equations from descriptions
3. **Multi-Agent Refinement** - Iteratively improve drawings through render → evaluate → refine
4. **Workflow Orchestration** - Coordinate all phases seamlessly
5. **Output & Visualization** - Deliver final equations and rendered images

```
User Prompt → Interpretation → Equation Generation → [Render → Evaluate → Refine]* → Final Image
                (Claude)            (Claude)              Multi-Agent Loop            (Matplotlib)
```

## Features

- **Natural Language to Math** - Converts descriptive text into parametric equations
- **Voice Input Support** - Optional voice-to-text via Vapi API
- **Iterative Refinement** - Self-improves drawings through multi-agent evaluation
- **RESTful API** - Easy integration with FastAPI backend
- **High-Quality Rendering** - Matplotlib-based visualization
- **Persistent Memory** - Optional Letta Cloud integration for session continuity

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Optional: Docker for containerized deployment

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CalHacks12
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:
   ```bash
   # Required
   ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # Optional
   VAPI_API_KEY=your_vapi_api_key_here
   LETTA_API_KEY=your_letta_api_key_here
   ```

   Get your Anthropic API key from [https://console.anthropic.com/](https://console.anthropic.com/)

5. **Run the server**
   ```bash
   uvicorn backend.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t parametric-drawing .
   ```

2. **Run the container**
   ```bash
   docker run -d -p 8000:8000 \
     -e ANTHROPIC_API_KEY=your_key_here \
     parametric-drawing:latest
   ```

## Usage

### API Endpoints

#### 1. Create Drawing from Text

```bash
POST /draw
Content-Type: application/json

{
  "prompt": "Draw a butterfly with symmetric wings",
  "use_letta": false
}
```

**Response:**
```json
{
  "success": true,
  "prompt": "Draw a butterfly with symmetric wings",
  "curves": {
    "curves": [
      {
        "name": "left_wing",
        "x": "cos(t) + 1",
        "y": "0.5*sin(2*t)",
        "t_min": 0,
        "t_max": 6.283185307179586,
        "color": "#FF4500"  // Note: Original color from Claude (for reference only)
      }
    ]
  },
  "relative_program": {
    "segments": [
      {
        "name": "left_wing",
        "x_rel": "1.00000000 * ( (cos(t) + 1) - 0.00000000 ) + 0.00000000 * ( (0.5*sin(2*t)) - 0.00000000 )",
        "y_rel": "0.00000000 * ( (cos(t) + 1) - 0.00000000 ) + 1.00000000 * ( (0.5*sin(2*t)) - 0.00000000 )",
        "t_min": 0.0,
        "t_max": 6.283185307179586,
        "pen": {
          "color": "#000000"  // Normalized: #FF4500 (orange-red) → #000000 (black)
        }
      }
    ]
  },
  "iterations": 2,
  "evaluation_score": 8.5,
  "image_base64": "data:image/png;base64,...",
  "processing_time": 4.2
}
```

> **Note**: The `relative_program` field contains the **preferred output format** for robot execution. Each segment is expressed in the local frame of where the previous segment ended. The robot executes segments sequentially without tracking global position. The `curves` field is maintained for backward compatibility.

#### 2. Create Drawing from Audio

```bash
POST /draw/audio
Content-Type: multipart/form-data

audio: <audio_file.wav>
use_letta: false
```

#### 3. Get Example Prompts

```bash
GET /examples
```

#### 4. Fetch Robot Program (NEW)

```bash
GET /robot/{run_id}
```

Fetch a previously generated relative motion plan for robot execution. The `run_id` is returned in the `stats` field of the `/draw` response.

**Example:**

```bash
# Step 1: Generate a drawing and get run_id
curl -X POST http://localhost:8000/draw \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Draw a butterfly"}'

# Response includes: "stats": {"run_id": "abc123...", "export_path": "exports/relative_program_abc123.json"}

# Step 2: Fetch the program on your robot (e.g., Raspberry Pi)
curl http://your-server:8000/robot/abc123...
```

**Response:**
```json
{
  "run_id": "abc123def456...",
  "prompt": "Draw a butterfly",
  "relative_program": {
    "segments": [
      {
        "name": "left_wing",
        "x_rel": "1.00000000 * ( (cos(t) + 1) - 0.00000000 ) + ...",
        "y_rel": "0.00000000 * ( (cos(t) + 1) - 0.00000000 ) + ...",
        "t_min": 0.0,
        "t_max": 6.28318531,
        "pen": {"color": "#000000"}  // Normalized to black or blue
      }
    ]
  }
}
```

**Features:**
- ✅ Durable storage in `exports/` directory
- ✅ Path-safe (no directory traversal)
- ✅ Lightweight caching (5 second max-age)
- ✅ 404 on missing run_id
- ✅ 400 on invalid run_id format

#### 5. Health Check

```bash
GET /health
```

### Python API

```python
from backend import pipeline

# Simple usage
result = pipeline.run_pipeline("Draw a heart shape")

if result["success"]:
    print(f"Generated {len(result['curves']['curves'])} curves")
    print(f"Image saved to: {result['image_path']}")
    print(f"Final score: {result['evaluation_score']}/10")
```

### Testing

Run the test suite:

```bash
python tests/test_sample_prompt.py
```

Run interactive mode:

```bash
python tests/test_sample_prompt.py --interactive
```

Test a specific prompt:

```bash
python tests/test_sample_prompt.py "Draw a spiral galaxy"
```

## Project Structure

```
CalHacks12/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── pipeline.py                # Main orchestrator
│   ├── schemas.py                 # Pydantic data models
│   ├── utils_relative.py          # Relative coordinate transformations
│   ├── claude_client.py           # Claude API integration
│   ├── vapi_client.py             # Vapi voice transcription
│   ├── renderer_agent.py          # Matplotlib rendering (absolute & relative)
│   ├── evaluator_agent.py         # Image evaluation
│   └── memory_manager.py          # State management
├── tests/
│   ├── test_sample_prompt.py      # Original test suite
│   ├── test_relative_chaining.py  # Relative transformation tests
│   ├── test_pen_color_default.py  # Pen color logic tests
│   ├── test_degenerate_derivative.py  # Edge case handling tests
│   └── test_response_schema.py    # Schema validation tests
├── static/                         # Generated images
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── .env.example                    # Environment template
└── README.md                       # This file
```

## How It Works

### Phase 1: Prompt Interpretation

Claude Sonnet 4.5 analyzes the prompt and extracts:
- Visual components (wings, body, petals, etc.)
- Symmetry type (vertical, horizontal, radial, none)
- Complexity rating (1-5)
- Detailed description

### Phase 2: Equation Generation

Claude generates parametric equations for each component:
- `x(t)` and `y(t)` expressions
- Parameter range `[t_min, t_max]`
- Color and styling information

Example for a circle:
```json
{
  "name": "circle",
  "x": "cos(t)",
  "y": "sin(t)",
  "t_min": 0,
  "t_max": 6.283185307179586,
  "color": "#4169E1"
}
```

### Phase 3: Multi-Agent Refinement

1. **Renderer Agent** - Plots equations using Matplotlib
2. **Evaluator Agent** - Scores the image (0-10) and provides feedback
3. **Refinement Agent** - Adjusts equations based on feedback
4. Repeat up to 3 iterations or until score ≥ 9

### Phase 4: Relative Program Generation

Transforms absolute parametric curves into a sequence of relative segments for robot execution:

1. **Compute End Poses** - Calculate position and orientation at the end of each curve segment
2. **Local Frame Transform** - Express each curve relative to the previous segment's end pose
3. **Pen Control** - Include pen color/state for each segment ("none" means pen up, no drawing)

The robot executes each segment in its own local frame without tracking global position. This approach is ideal for robots without localization systems.

### Phase 5: Output

Returns:
- **Relative Program** (NEW, preferred) - Sequence of curves in local frames with pen control
- **Absolute Curves** (legacy) - Original global parametric equations for backward compatibility
- Rendered image (base64 or file path)
- Evaluation metrics
- Processing statistics

## Example Prompts

| Prompt | Complexity | Description |
|--------|-----------|-------------|
| "Draw a circle" | 1 | Simple geometric shape |
| "Draw a heart shape" | 2 | Classic symmetric heart |
| "Draw a butterfly" | 3 | Mirrored wing patterns |
| "Draw a flower with 5 petals" | 3 | Radial symmetry |
| "Draw a spiral galaxy" | 4 | Logarithmic spiral |
| "Draw a Celtic knot" | 5 | Intricate patterns |

## API Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from Anthropic |
| `VAPI_API_KEY` | No | Vapi voice API key (for audio input) |
| `LETTA_API_KEY` | No | Letta Cloud API key (for persistent memory) |
| `PORT` | No | Server port (default: 8000) |

## Technical Details

### Parametric Equations

All curves are defined parametrically:
- **x(t)**: Expression for x-coordinate as a function of parameter t
- **y(t)**: Expression for y-coordinate as a function of parameter t
- **t**: Parameter typically ranging from 0 to 2π

Supported functions:
- Trigonometric: `sin`, `cos`, `tan`
- Other: `sqrt`, `exp`, `abs`, `log`
- Constants: `pi`, `e`

### Relative Program Format (NEW)

The `relative_program` field contains a sequence of parametric curve segments expressed in **local coordinate frames**. This format is designed for robots that execute movements relative to their current pose without requiring global localization.

#### Structure

```json
{
  "relative_program": {
    "segments": [
      {
        "name": "segment_name",
        "x_rel": "mathematical expression in t (relative x)",
        "y_rel": "mathematical expression in t (relative y)",
        "t_min": 0.0,
        "t_max": 6.28318531,
        "pen": {
          "color": "#FF4500"  // or "none" for pen up
        }
      }
    ]
  }
}
```

#### Mathematical Transformation

Each segment i+1 is expressed relative to the end pose of segment i:

Given absolute curves C_i with (x_i(t), y_i(t)), the system:

1. **Computes end pose** P_i = (x_end, y_end, θ_end) where:
   - x_end = x_i(t_max)
   - y_end = y_i(t_max)
   - θ_end = atan2(y'_i(t_max), x'_i(t_max))

2. **Transforms to local frame** using rotation matrix:
   ```
   [x_rel]   [cos(-θ)  -sin(-θ)] ([x(t)]   [x_prev])
   [y_rel] = [sin(-θ)   cos(-θ)] ([y(t)] - [y_prev])
   ```

3. **Embeds as string expressions** with numerical constants (8 decimal precision)

#### Robot Execution Model

Robots should execute the relative program as follows:

```python
# Pseudocode for robot execution
current_pose = (0, 0, 0)  # Start at origin

for segment in relative_program.segments:
    if segment.pen.color == "none":
        # Pen up - move without drawing
        execute_motion(segment, draw=False)
    else:
        # Pen down - draw with specified color
        set_pen_color(segment.pen.color)
        execute_motion(segment, draw=True)

    # Robot's local frame automatically becomes (0,0,0)
    # for the next segment
```

**Key principle**: The robot does NOT track or maintain global position. Each segment is executed in a fresh local frame that starts at (0, 0, 0).

#### Pen Control

**Automatic Color Normalization:**

All pen colors are automatically normalized to exactly one of three values:
- **`"none"`** - Pen up (travel move, no drawing)
- **`"#000000"`** - Black (pen down, drawing)
- **`"#0000FF"`** - Blue (pen down, drawing)

**Color Mapping:**
- Any input color is mapped to the nearest of black or blue using RGB distance
- Example: `#FF0000` (red) → `#000000` (black)
- Example: `#4169E1` (royal blue) → `#0000FF` (blue)
- Example: `#00FFFF` (cyan) → `#0000FF` (blue)

**Defaults:**
- Drawing segments without explicit color: `"#000000"` (black)
- Travel segments (disconnected curves): `"none"` (pen up)
- Invalid/missing colors: `"#000000"` (black)

This restriction ensures compatibility with dual-pen robot systems that support only black and blue inks.

### Robot Fetch API

The system provides durable storage and retrieval of robot programs:

#### Flow

1. **POST /draw** generates a drawing and returns:
   - `stats.run_id`: Unique identifier (32-char hex UUID)
   - `stats.export_path`: Path to exported JSON file
   - `relative_program`: Inline program (for immediate use)

2. **Automatic Export**: Each run is saved to `exports/relative_program_{run_id}.json`

3. **GET /robot/{run_id}** retrieves the stored program:
   - Returns: `{run_id, prompt, relative_program}`
   - Safe: Path sanitization prevents directory traversal
   - Cached: 5-second max-age to reduce file I/O

#### Export File Format

```json
{
  "run_id": "abc123def456...",
  "prompt": "Draw a butterfly",
  "relative_program": {
    "segments": [...]
  }
}
```

Stored at: `exports/relative_program_{run_id}.json`

#### Robot Integration Example

```python
import requests

# On server: Generate drawing
response = requests.post("http://server:8000/draw",
                         json={"prompt": "Draw a star"})
run_id = response.json()["stats"]["run_id"]

# On robot (Raspberry Pi): Fetch program
program = requests.get(f"http://server:8000/robot/{run_id}").json()
execute_drawing(program["relative_program"])
```

### Safety

Mathematical expressions are evaluated in a restricted context:
- Only whitelisted functions allowed
- No arbitrary code execution
- Input validation on all endpoints

## Limitations

1. **Visual Evaluation**: Currently uses heuristic-based evaluation. Production would integrate actual vision AI (Claude with vision, GPT-4V).

2. **Voice Input**: Vapi integration requires additional API setup. Text input works out of the box.

3. **Complexity**: Very complex shapes (5/5 complexity) may require manual equation adjustments.

4. **Real-time**: Processing takes 3-10 seconds depending on complexity and number of iterations.

## Future Enhancements

- [ ] Integrate actual vision AI for evaluation (Claude Vision API)
- [ ] Full Vapi voice transcription implementation
- [ ] Letta Cloud persistent memory across sessions
- [ ] Composio tool routing for dynamic workflow
- [ ] 3D parametric surfaces
- [ ] Animation support (parametric curves over time)
- [ ] Desmos graph export
- [ ] Color gradient support
- [ ] Interactive web frontend

## Troubleshooting

### API Key Issues

```
Error: ANTHROPIC_API_KEY environment variable is required
```

**Solution**: Set your Anthropic API key in the `.env` file or environment.

### Import Errors

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution**: Install dependencies with `pip install -r requirements.txt`

### Port Already in Use

```
Error: [Errno 48] Address already in use
```

**Solution**: Change the port with `uvicorn backend.main:app --port 8001`

### Image Not Rendering

**Solution**: Ensure the `static/` directory exists and has write permissions.

## Contributing

This is a hackathon project for Cal Hacks 12.0. Contributions, suggestions, and feedback are welcome!

## Acknowledgments

Built with technologies from Cal Hacks 12.0 sponsors:
- [Anthropic](https://anthropic.com) - Claude Sonnet 4.5 AI
- [Vapi](https://vapi.ai) - Voice AI
- [Letta](https://letta.com) - Persistent memory
- [Fetch.ai](https://fetch.ai) - Agent framework
- [Composio](https://composio.dev) - Tool integration

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Built for Cal Hacks 12.0** 🚀

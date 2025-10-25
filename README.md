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
        "color": "#FF4500"
      },
      ...
    ]
  },
  "iterations": 2,
  "evaluation_score": 8.5,
  "image_base64": "data:image/png;base64,...",
  "processing_time": 4.2
}
```

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

#### 4. Health Check

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
│   ├── main.py                 # FastAPI application
│   ├── pipeline.py             # Main orchestrator
│   ├── claude_client.py        # Claude API integration
│   ├── vapi_client.py          # Vapi voice transcription
│   ├── renderer_agent.py       # Matplotlib rendering
│   ├── evaluator_agent.py      # Image evaluation
│   └── memory_manager.py       # State management
├── tests/
│   └── test_sample_prompt.py   # Test suite
├── static/                      # Generated images
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── .env.example                 # Environment template
└── README.md                    # This file
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

### Phase 4: Output

Returns:
- Final parametric equations
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

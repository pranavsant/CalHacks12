# Implementation Details

This document provides detailed information about the implementation of the Parametric Curve Drawing System.

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (Text/Voice)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 1: Input Processing                       │
│  ┌──────────────┐         ┌────────────────────────────┐   │
│  │ Vapi Client  │────────▶│   Claude API Client        │   │
│  │ (Optional)   │         │   (Prompt Interpretation)  │   │
│  └──────────────┘         └────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ Structured Description
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Phase 2: Parametric Equation Generation             │
│                 ┌────────────────────────────┐              │
│                 │   Claude API Client        │              │
│                 │   (Equation Generation)    │              │
│                 └────────────────────────────┘              │
└────────────────────────┬────────────────────────────────────┘
                         │ Initial Equations
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      Phase 3: Multi-Agent Refinement Loop (Max 3x)          │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ Renderer Agent │─▶│ Evaluator Agent  │─▶│ Refiner    │ │
│  │  (Matplotlib)  │  │  (Image Analysis)│  │ (Claude)   │ │
│  └────────────────┘  └──────────────────┘  └─────┬──────┘ │
│         ▲                                          │         │
│         └──────────────────────────────────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │ Final Equations + Image
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Phase 4: Output & Visualization                 │
│        ┌────────────────────────────────────────┐           │
│        │ JSON Response with Image (Base64/Path) │           │
│        └────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### 1. backend/main.py (FastAPI Application)

**Purpose**: HTTP API server and entry point

**Key Components**:
- FastAPI app initialization with CORS middleware
- Endpoints:
  - `POST /draw` - Text-based drawing
  - `POST /draw/audio` - Voice-based drawing
  - `GET /health` - Health check
  - `GET /examples` - Example prompts
- Error handling and validation
- Static file serving for images

**Technologies**:
- FastAPI (web framework)
- Pydantic (data validation)
- Uvicorn (ASGI server)

### 2. backend/claude_client.py (Claude API Integration)

**Purpose**: All interactions with Anthropic's Claude API

**Key Functions**:

1. **`interpret_prompt(prompt_text)`**
   - Takes natural language prompt
   - Returns structured JSON with:
     - Description
     - Visual components
     - Symmetry type
     - Complexity (1-5)

2. **`generate_parametric_equations(description)`**
   - Takes structured description
   - Returns curves JSON with:
     - x(t), y(t) expressions
     - Parameter ranges
     - Colors and styling

3. **`refine_equations(current_equations, feedback)`**
   - Takes existing equations and evaluation feedback
   - Returns improved equations

**Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

**Configuration**:
- Temperature: 0-0.2 (deterministic to slightly creative)
- Max tokens: 500-1500 depending on task
- System prompts guide output format

### 3. backend/renderer_agent.py (Matplotlib Rendering)

**Purpose**: Convert parametric equations to visual images

**Key Functions**:

1. **`safe_eval_expression(expr, t_value)`**
   - Safely evaluates mathematical expressions
   - Restricted context (only math functions)
   - No arbitrary code execution

2. **`plot_curve(ax, curve, num_points=1000)`**
   - Plots a single parametric curve
   - Samples 1000 points for smoothness
   - Handles edge cases (NaN, infinity)

3. **`render_curves(curves_dict)`**
   - Main rendering function
   - Creates figure with proper aspect ratio
   - Saves to PNG file
   - Returns file path

**Configuration**:
- Figure size: 8x8 inches
- DPI: 100 (high quality)
- Backend: Agg (non-GUI)
- Aspect ratio: Equal (prevents distortion)

### 4. backend/evaluator_agent.py (Image Evaluation)

**Purpose**: Evaluate rendered images against original intent

**Current Implementation**: Heuristic-based stub

**Key Functions**:

1. **`check_symmetry(image_path, symmetry_type)`**
   - Uses PIL and NumPy
   - Compares image halves
   - Returns symmetry score (0-10)

2. **`evaluate_image(image_path, prompt_text, description, iteration_number)`**
   - Main evaluation function
   - Returns (score, feedback) tuple
   - Progressive improvement simulation

**Scores by Iteration**:
- Iteration 1: ~7.0 (moderate, suggests improvements)
- Iteration 2: ~8.5 (improved)
- Iteration 3+: ~9.0 (high score to stop refinement)

**Future Enhancement**: Integrate actual vision AI (Claude Vision, GPT-4V)

### 5. backend/memory_manager.py (State Management)

**Purpose**: Track state across pipeline phases and iterations

**Classes**:

1. **`MemoryManager`**
   - Basic in-memory state tracking
   - Stores prompts, equations, evaluations, images
   - Session-based organization
   - JSON export/import

2. **`LettaMemoryManager`** (extends MemoryManager)
   - Placeholder for Letta Cloud integration
   - Persistent memory across sessions
   - Agent-based state management

**Storage Structure**:
```python
{
  "session_id": "session_20251025_123456",
  "current_state": {
    "prompt": "...",
    "description": {...},
    "equations": {...},
    "iteration": 2
  },
  "history": [
    {"type": "initial_prompt", "timestamp": "...", ...},
    {"type": "equations", "iteration": 1, ...},
    {"type": "evaluation", "score": 7.5, ...},
    ...
  ]
}
```

### 6. backend/pipeline.py (Orchestrator)

**Purpose**: Main workflow controller

**Key Components**:

1. **`Pipeline` Class**
   - Coordinates all phases
   - Manages refinement loop
   - Tracks timing and metrics

2. **`run_pipeline(prompt_text)`**
   - Main entry point
   - Returns complete result dictionary

3. **`_refinement_loop(initial_curves, prompt_text, description)`**
   - Iterative improvement
   - Max 3 iterations
   - Stops if score ≥ 9.0

**Flow**:
```python
1. Interpret prompt (Claude)
2. Generate equations (Claude)
3. Loop (max 3 iterations):
   a. Render curves (Matplotlib)
   b. Evaluate image (Evaluator)
   c. If score < target and iterations remain:
      - Refine equations (Claude)
      - Continue loop
4. Prepare final output
```

### 7. backend/vapi_client.py (Voice Transcription)

**Purpose**: Convert audio to text using Vapi

**Status**: Placeholder implementation

**Key Function**:
- `transcribe_audio(audio_path)` - Currently raises NotImplementedError

**Note**: Requires actual Vapi API integration. Text input works without this.

## Data Flow

### Request Format

```json
{
  "prompt": "Draw a butterfly with symmetric wings",
  "use_letta": false
}
```

### Response Format

```json
{
  "success": true,
  "prompt": "Draw a butterfly with symmetric wings",
  "description": {
    "description": "A butterfly with mirror-symmetric wings...",
    "components": ["left_wing", "right_wing", "body", "antennae"],
    "symmetry": "vertical",
    "complexity": 3
  },
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
  "evaluation_feedback": "Drawing shows improvement...",
  "image_path": "static/output_20251025_123456_abc12345.png",
  "image_base64": "data:image/png;base64,...",
  "processing_time": 4.2,
  "session_id": "session_20251025_123456",
  "history": [...]
}
```

## Configuration

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| ANTHROPIC_API_KEY | Yes | - | Claude API authentication |
| VAPI_API_KEY | No | - | Vapi voice API (optional) |
| LETTA_API_KEY | No | - | Letta Cloud memory (optional) |
| PORT | No | 8000 | Server port |

### Pipeline Parameters

```python
# In backend/pipeline.py
MAX_ITERATIONS = 3      # Maximum refinement loops
TARGET_SCORE = 9.0      # Score to stop early

# In backend/renderer_agent.py
NUM_POINTS = 1000       # Points sampled per curve
FIGURE_SIZE = (8, 8)    # Image dimensions
DPI = 100               # Image resolution
```

## Testing

### Test Files

1. **tests/test_sample_prompt.py**
   - Automated test suite
   - Multiple test cases
   - Interactive mode

2. **example_client.py**
   - Demonstrates API usage
   - HTTP request examples
   - Image saving

### Running Tests

```bash
# Full test suite
python tests/test_sample_prompt.py

# Interactive mode
python tests/test_sample_prompt.py --interactive

# Single prompt
python tests/test_sample_prompt.py "Draw a circle"

# Example client
python example_client.py
```

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
./run_server.sh
# or
uvicorn backend.main:app --reload
```

### Docker Deployment

```bash
# Build image
docker build -t parametric-drawing .

# Run container
docker run -d -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key \
  parametric-drawing:latest
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Performance

### Typical Processing Times

| Complexity | Iterations | Time (seconds) |
|------------|-----------|----------------|
| 1 (Circle) | 1-2 | 2-4 |
| 3 (Butterfly) | 2-3 | 4-8 |
| 5 (Complex) | 3 | 8-15 |

### Bottlenecks

1. **Claude API calls**: 1-2 seconds each
2. **Image rendering**: <0.5 seconds
3. **Image evaluation**: <0.5 seconds (stub)

### Optimization Opportunities

- Cache common prompts/equations
- Parallel evaluation if using real vision AI
- Reduce iteration count for simpler shapes
- Optimize equation complexity

## Security

### Input Validation

- Prompts limited to reasonable length
- Audio files size-limited
- File type validation for uploads

### Expression Evaluation

- Whitelist of allowed functions
- No `__builtins__` access
- Sandboxed eval context

### API Security

- CORS configured (set specific origins in production)
- No SQL injection (no database)
- No command injection (safe subprocess usage)

## Error Handling

### Common Errors

1. **Missing API Key**: Returns 500 with clear message
2. **Invalid Prompt**: Returns 400 with validation error
3. **Claude API Error**: Caught and returns fallback/error
4. **Rendering Error**: Logged and returns error response

### Graceful Degradation

- If Claude fails to parse JSON: fallback to simple shapes
- If rendering fails: detailed error logged
- If refinement fails: return previous iteration

## Future Enhancements

### Short-term

- [ ] Integrate actual vision AI (Claude Vision API when available)
- [ ] Complete Vapi voice transcription
- [ ] Add more curve examples to prompt library

### Medium-term

- [ ] Full Letta Cloud integration
- [ ] Composio tool routing
- [ ] Web frontend (React + Vite)
- [ ] Real-time streaming of iterations

### Long-term

- [ ] 3D parametric surfaces
- [ ] Animation support (curves over time)
- [ ] Collaborative drawing sessions
- [ ] Fine-tuned model for equation generation

## Troubleshooting

See [README.md](README.md#troubleshooting) for common issues and solutions.

## References

- [Anthropic Claude API Docs](https://docs.anthropic.com/)
- [Vapi Documentation](https://docs.vapi.ai/)
- [Letta Documentation](https://docs.letta.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Matplotlib Documentation](https://matplotlib.org/)

---

**Last Updated**: 2025-10-25
**Version**: 1.0.0

# Parametric Drawing Generator

> Transform natural language and voice prompts into mathematical parametric curves and rendered images using AI.

**Built for Cal Hacks 12.0** 🚀

![Architecture](https://img.shields.io/badge/Frontend-Next.js_16-black?logo=next.js)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![AI](https://img.shields.io/badge/AI-Claude_Sonnet_4.5-8B5CF6)

---

## ✨ What It Does

Describe an image with **text** or **voice**, and watch AI generate it using parametric equations:

- 🎨 **Natural Language to Math** - "Draw a butterfly" → parametric curves
- 🎤 **Voice Input Support** - Record or upload audio descriptions
- 🔄 **Iterative Refinement** - AI self-improves drawings through multi-agent evaluation
- 🤖 **Robot-Ready Output** - Generate programs for physical drawing robots
- 🖼️ **Beautiful Visualization** - High-quality rendered images

---

## 🚀 Quick Start (Run the Full Application)

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Anthropic API Key** ([Get one here](https://console.anthropic.com/))

### 1. Clone & Set Up Environment

```bash
# Clone the repository
git clone <repository-url>
cd CalHacks12

# Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Install Dependencies

#### Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

#### Frontend:
```bash
cd frontend
npm install
cd ..
```

### 3. Run the Application

**Option A: Two Terminal Windows (Recommended)**

Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

**Option B: Using tmux (Advanced)**
```bash
# Start backend in background pane
tmux new-session -d -s calhacks 'cd backend && source venv/bin/activate && uvicorn app.main:app --reload'
# Start frontend in foreground
tmux split-window -h 'cd frontend && npm run dev'
tmux attach -t calhacks
```

### 4. Open Your Browser

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 5. Try It Out!

1. Type a prompt: `"Draw a spiral flower with 5 petals"`
2. Or record audio: Click the microphone button and describe your image
3. Hit **"Generate Drawing"**
4. Watch the AI create parametric equations and render your image!

---

## 📁 Project Structure

```
CalHacks12/
├── frontend/                    # Next.js web application
│   ├── app/
│   │   ├── page.tsx            # Main page component
│   │   └── api/draw/route.ts   # API proxy to backend
│   ├── components/
│   │   ├── drawing-input.tsx   # Input form (text/voice)
│   │   └── drawing-results.tsx # Results display
│   ├── types/drawing.ts        # TypeScript interfaces
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── pipeline.py         # Main orchestration pipeline
│   │   ├── schemas.py          # Pydantic data models
│   │   ├── claude_client.py    # Claude AI integration
│   │   ├── renderer_agent.py   # Image rendering
│   │   ├── evaluator_agent.py  # Quality evaluation
│   │   └── utils_relative.py   # Robot coordinate transforms
│   ├── static/                 # Generated images (runtime)
│   ├── exports/                # Robot programs (runtime)
│   ├── requirements.txt
│   └── Dockerfile
│
├── tests/                       # Test suite
├── .env.example                 # Environment template
├── .env                         # Your secrets (git-ignored)
└── README.md                    # This file
```

---

## 🛠️ Development Setup

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (in project root `.env`):
   ```bash
   # Required
   ANTHROPIC_API_KEY=sk-ant-...

   # Optional
   VAPI_API_KEY=your_vapi_key      # For voice transcription
   LETTA_API_KEY=your_letta_key    # For persistent memory
   PORT=8000                        # Backend port (default: 8000)
   ```

4. **Run backend:**
   ```bash
   # Development mode with auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

   # Or use the provided script:
   bash scripts/run_server.sh
   ```

5. **Verify it's running:**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure backend URL** (optional):

   Create `frontend/.env.local` if you need to change the backend URL:
   ```bash
   BACKEND_URL=http://localhost:8000
   ```

   **Default:** If not set, it uses `http://localhost:8000`

3. **Run frontend:**
   ```bash
   npm run dev
   ```

4. **Verify it's running:**
   - Frontend: http://localhost:3000

### Running Both Together

**Recommended workflow:**

1. Start backend first (wait for "Application startup complete")
2. Start frontend second
3. Frontend will automatically connect to backend at `http://localhost:8000`

**Troubleshooting Connection:**
- ✅ Backend running? Check http://localhost:8000/health
- ✅ Frontend running? Check http://localhost:3000
- ✅ CORS enabled? (Backend automatically allows all origins in dev mode)
- ✅ Ports not in use? Change with `--port` or `PORT` env var

---

## 🎯 How to Use

### Text Input

1. Open http://localhost:3000
2. Type your prompt: `"Draw a heart shape"`
3. Optionally toggle "Use Letta Memory" for contextual awareness
4. Click **"Generate Drawing"**
5. View your image, parametric equations, and AI evaluation score!

### Voice Input

1. Click the **"Record Audio"** button (grant microphone permission)
2. Describe your image: *"Draw a butterfly with rainbow wings"*
3. Click **"Stop Recording"**
4. The system will transcribe and generate your drawing
5. See the transcribed prompt displayed with your image

**Or upload an audio file:**
1. Click **"Upload Audio"**
2. Select a .wav, .mp3, or other audio file
3. Generate!

---

## 🏗️ Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  (Next.js 16 + React 19 + Tailwind CSS + shadcn/ui)       │
│                                                             │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │ Text Input   │      │ Voice Input  │                   │
│  │  Component   │      │  Component   │                   │
│  └──────┬───────┘      └──────┬───────┘                   │
│         │                     │                            │
│         └─────────┬───────────┘                            │
│                   │                                        │
│         ┌─────────▼──────────┐                             │
│         │   API Route        │                             │
│         │  /api/draw         │                             │
│         └─────────┬──────────┘                             │
└───────────────────┼─────────────────────────────────────┘
                    │ HTTP POST
                    │
┌───────────────────▼─────────────────────────────────────┐
│                      BACKEND                             │
│            (FastAPI + Python 3.11)                       │
│                                                           │
│  ┌─────────────┐         ┌─────────────┐                │
│  │ POST /draw  │         │POST /draw/  │                │
│  │   (text)    │         │   audio     │                │
│  └──────┬──────┘         └──────┬──────┘                │
│         │                       │                        │
│         │    ┌──────────────────┘                        │
│         │    │                                           │
│    ┌────▼────▼────┐                                      │
│    │   Pipeline   │                                      │
│    └────┬─────────┘                                      │
│         │                                                │
│    ┌────▼──────────────────────────────────┐            │
│    │  Phase 1: Prompt Interpretation       │            │
│    │           (Claude)                    │            │
│    └────┬──────────────────────────────────┘            │
│         │                                                │
│    ┌────▼──────────────────────────────────┐            │
│    │  Phase 2: Equation Generation         │            │
│    │           (Claude)                    │            │
│    └────┬──────────────────────────────────┘            │
│         │                                                │
│    ┌────▼──────────────────────────────────┐            │
│    │  Phase 3: Multi-Agent Refinement      │            │
│    │   ┌────────────────────────┐          │            │
│    │   │ Render → Evaluate →    │          │            │
│    │   │ Refine (up to 3x)      │          │            │
│    │   └────────────────────────┘          │            │
│    └────┬──────────────────────────────────┘            │
│         │                                                │
│    ┌────▼──────────────────────────────────┐            │
│    │  Phase 4: Relative Program Gen        │            │
│    │   (Robot coordinate transforms)       │            │
│    └────┬──────────────────────────────────┘            │
│         │                                                │
│    ┌────▼──────────────────────────────────┐            │
│    │  Phase 5: Return Results              │            │
│    │  - Image (base64)                     │            │
│    │  - Parametric equations               │            │
│    │  - Robot program                      │            │
│    │  - Evaluation score                   │            │
│    └───────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- **Framework:** Next.js 16 (App Router) + React 19
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Audio:** Web Audio API + MediaRecorder
- **Type Safety:** TypeScript 5

**Backend:**
- **Framework:** FastAPI (Python 3.11)
- **AI:** Anthropic Claude Sonnet 4.5
- **Rendering:** Matplotlib
- **Voice (Optional):** Vapi API
- **Memory (Optional):** Letta Cloud
- **Data Validation:** Pydantic v2

---

## 📡 API Reference

### Frontend → Backend Flow

#### Text Input Flow:
```
POST /api/draw
Content-Type: application/json

{
  "prompt": "Draw a circle",
  "use_letta": false
}
↓
Backend: POST http://localhost:8000/draw
↓
Response: DrawingResponse
```

#### Audio Input Flow:
```
POST /api/draw
Content-Type: multipart/form-data

FormData {
  file: Blob (audio),
  use_letta: "false"
}
↓
Backend: POST http://localhost:8000/draw/audio
FormData {
  audio: Blob,
  use_letta: "false"
}
↓
Response: DrawingResponse (with transcribed prompt)
```

### Backend Endpoints

**Full API documentation:** http://localhost:8000/docs

#### `POST /draw`
Create drawing from text prompt.

**Request:**
```json
{
  "prompt": "Draw a spiral galaxy",
  "use_letta": false
}
```

**Response:**
```json
{
  "success": true,
  "prompt": "Draw a spiral galaxy",
  "image_base64": "data:image/png;base64,...",
  "relative_program": {
    "segments": [
      {
        "name": "spiral_arm",
        "x_rel": "t*cos(t)",
        "y_rel": "t*sin(t)",
        "t_min": 0,
        "t_max": 12.566,
        "pen": { "color": "#000000" }
      }
    ]
  },
  "evaluation_score": 8.5,
  "iterations": 2,
  "processing_time": 4.2,
  "stats": {
    "run_id": "abc123...",
    "export_path": "exports/relative_program_abc123.json"
  }
}
```

#### `POST /draw/audio`
Create drawing from audio file.

**Request:**
```bash
curl -X POST http://localhost:8000/draw/audio \
  -F "audio=@recording.wav" \
  -F "use_letta=false"
```

**Response:** Same as `/draw`, with transcribed prompt

#### `GET /robot/{run_id}`
Fetch robot program for physical drawing.

**Response:**
```json
{
  "run_id": "abc123...",
  "prompt": "Draw a star",
  "relative_program": { ... }
}
```

#### `GET /health`
Check system status.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "anthropic_claude": "configured",
    "vapi_voice": "not_configured",
    "letta_memory": "not_configured"
  }
}
```

---

## 🎨 Understanding the Output

### Generated Image
The AI creates a mathematical drawing rendered as a PNG image, displayed in the frontend.

### Prompt Display
Shows the exact prompt used (especially useful for voice input to confirm transcription).

### Parametric Equations
**Relative Program Segments** (preferred for robots):
```
spiral_arm:
  x(t) = t*cos(t)
  y(t) = t*sin(t)
  t ∈ [0.00, 12.57]
  Color: Black
```

Each segment is expressed in **local coordinates** relative to the previous segment's end position. Perfect for robots without global localization!

### Evaluation Score
AI scores the drawing from 0-10 based on how well it matches the prompt:
- **9-10:** Excellent match
- **7-8:** Good match
- **5-6:** Acceptable
- **<5:** Needs improvement

### Iterations
Number of refinement cycles the AI performed (max 3).

---

## 🧪 Testing

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
python -m pytest tests/

# Test a specific prompt
python tests/test_sample_prompt.py "Draw a heart"

# Interactive mode
python tests/test_sample_prompt.py --interactive
```

### Frontend Testing

```bash
cd frontend
npm run build  # Ensure no build errors
npm run lint   # Check for linting issues
```

### End-to-End Testing

1. Start both backend and frontend
2. **Test Text Input:**
   - Enter: `"Draw a circle"`
   - Verify image appears
   - Check parametric equations displayed
   - Confirm score and iterations shown

3. **Test Voice Input:**
   - Click "Record Audio"
   - Say: *"Draw a flower with 5 petals"*
   - Stop recording
   - Verify transcription appears
   - Check drawing generated

4. **Test Error Handling:**
   - Stop backend
   - Try to generate a drawing
   - Verify user-friendly error message appears
   - Restart backend
   - Verify recovery

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# === REQUIRED ===
ANTHROPIC_API_KEY=sk-ant-...

# === OPTIONAL ===
# Voice transcription (Vapi)
VAPI_API_KEY=your_vapi_key

# Persistent memory across sessions (Letta)
LETTA_API_KEY=your_letta_key

# Backend port
PORT=8000
```

### Frontend Configuration

Create `frontend/.env.local` (optional):

```bash
# Backend URL (default: http://localhost:8000)
BACKEND_URL=http://localhost:8000

# For production deployment:
# BACKEND_URL=https://your-backend.com
```

---

## 🐳 Docker Deployment

### Backend Only

```bash
cd backend
docker build -t parametric-drawing-backend .
docker run -d -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  parametric-drawing-backend
```

### Full Stack (docker-compose)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./backend/static:/app/static
      - ./backend/exports:/app/exports

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

Run:
```bash
docker-compose up -d
```

---

## 🤖 Robot Integration

The system generates **relative motion programs** for physical drawing robots.

### How It Works

1. Generate a drawing via `/draw` endpoint
2. Backend returns `stats.run_id` and exports program to `exports/`
3. Robot fetches program via `GET /robot/{run_id}`
4. Robot executes segments sequentially in local coordinates

### Example Robot Code

```python
import requests
import math

# 1. Generate drawing on server
response = requests.post("http://server:8000/draw",
                         json={"prompt": "Draw a star"})
data = response.json()
run_id = data["stats"]["run_id"]

# 2. On robot: Fetch program
program = requests.get(f"http://server:8000/robot/{run_id}").json()

# 3. Execute each segment
for segment in program["relative_program"]["segments"]:
    if segment["pen"]["color"] == "none":
        # Pen up - travel move
        move_without_drawing(segment)
    else:
        # Pen down - draw with specified color
        set_pen_color(segment["pen"]["color"])
        draw_parametric_curve(
            x_expr=segment["x_rel"],
            y_expr=segment["y_rel"],
            t_min=segment["t_min"],
            t_max=segment["t_max"]
        )
    # Local frame automatically resets to (0,0,0) for next segment
```

### Pen Colors (Normalized)

All colors are automatically mapped to:
- `"none"` - Pen up (no drawing)
- `"#000000"` - Black pen
- `"#0000FF"` - Blue pen

Perfect for dual-pen robot systems!

---

## 📚 Example Prompts

| Prompt | Complexity | Expected Result |
|--------|-----------|-----------------|
| `"Draw a circle"` | ⭐ | Perfect circle |
| `"Draw a heart shape"` | ⭐⭐ | Symmetric heart |
| `"Draw a butterfly with symmetric wings"` | ⭐⭐⭐ | Butterfly with mirrored wings |
| `"Draw a flower with 5 petals"` | ⭐⭐⭐ | 5-petal radial flower |
| `"Draw a spiral galaxy"` | ⭐⭐⭐⭐ | Logarithmic spiral |
| `"Draw a Celtic knot"` | ⭐⭐⭐⭐⭐ | Intricate interwoven pattern |

---

## 🐛 Troubleshooting

### Frontend won't connect to backend

**Symptom:** "Failed to generate drawing" error

**Solutions:**
1. ✅ Check backend is running: `curl http://localhost:8000/health`
2. ✅ Check `BACKEND_URL` in `frontend/.env.local` (default: `http://localhost:8000`)
3. ✅ Check CORS in backend logs (should allow all origins in dev)
4. ✅ Check browser console for network errors

### "ANTHROPIC_API_KEY not found"

**Solution:**
```bash
# Check .env file exists in project root
cat .env

# Should contain:
ANTHROPIC_API_KEY=sk-ant-...

# Restart backend after adding key
```

### Port Already in Use

**Symptom:** `Address already in use` error

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### Microphone Access Denied

**Solution:**
1. Check browser permissions (URL bar → lock icon → permissions)
2. Allow microphone access
3. Refresh page

### "Module not found" errors

**Backend:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Images not appearing

**Solution:**
1. Check `backend/static/` directory exists and is writable
2. Check backend logs for rendering errors
3. Verify image data in browser DevTools → Network tab
4. Check console for image loading errors

---

## 🚀 Production Deployment

### Environment Setup

**Backend:**
- Set `ANTHROPIC_API_KEY` in production environment
- Use `gunicorn` or `uvicorn` with production settings
- Configure proper CORS origins (not wildcard)
- Set up HTTPS with reverse proxy (nginx/Caddy)

**Frontend:**
- Set `BACKEND_URL` to production backend URL
- Build with `npm run build`
- Serve with `npm start` or deploy to Vercel/Netlify

### Recommended Stack

- **Backend:** Railway, Render, Fly.io, or AWS ECS
- **Frontend:** Vercel, Netlify, or Cloudflare Pages
- **Storage:** Mount persistent volumes for `static/` and `exports/`

---

## 🎓 How It Works (Under the Hood)

### Phase 1: Prompt Interpretation
Claude Sonnet 4.5 analyzes your prompt to extract:
- Visual components (e.g., "wings", "body", "petals")
- Symmetry type (vertical, horizontal, radial, none)
- Complexity rating (1-5 scale)
- Detailed structural description

### Phase 2: Equation Generation
Claude generates mathematical parametric equations:
- `x(t)` and `y(t)` expressions using trig functions
- Parameter range `[t_min, t_max]`
- Color information

**Example (Circle):**
```json
{
  "name": "circle",
  "x": "cos(t)",
  "y": "sin(t)",
  "t_min": 0,
  "t_max": 6.283185307179586
}
```

### Phase 3: Multi-Agent Refinement
Iterative improvement loop (up to 3 iterations):

1. **Renderer Agent:** Plots equations using Matplotlib
2. **Evaluator Agent:** Scores image 0-10, provides feedback
3. **Refinement Agent:** Adjusts equations based on feedback
4. Repeat until score ≥ 9 or max iterations reached

### Phase 4: Relative Program Generation
Transforms absolute curves into robot-ready format:

1. **Compute End Poses:** Calculate (x, y, θ) at end of each curve
2. **Local Frame Transform:** Express each curve relative to previous end pose
3. **Pen Control:** Assign normalized colors (`"none"`, `"#000000"`, `"#0000FF"`)

**Mathematical Transform:**
```
[x_rel]   [cos(-θ)  -sin(-θ)] ([x(t)]   [x_prev])
[y_rel] = [sin(-θ)   cos(-θ)] ([y(t)] - [y_prev])
```

### Phase 5: Output
Returns comprehensive results:
- Rendered image (base64 PNG with data URI)
- Relative program (robot-ready segments)
- Evaluation score and feedback
- Processing metadata

---

## 📖 Additional Resources

- **Backend API Docs:** http://localhost:8000/docs (when running)
- **Anthropic Claude:** https://www.anthropic.com/claude
- **Next.js Documentation:** https://nextjs.org/docs
- **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## 🙏 Acknowledgments

Built with technologies from **Cal Hacks 12.0** sponsors:
- [Anthropic](https://anthropic.com) - Claude Sonnet 4.5 AI
- [Vapi](https://vapi.ai) - Voice-to-text API
- [Letta](https://letta.com) - Persistent memory
- [Fetch.ai](https://fetch.ai) - Agent framework concepts
- [Composio](https://composio.dev) - Tool integration patterns

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🤝 Contributing

This is a hackathon project, but contributions, suggestions, and feedback are welcome! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests
- Share your generated drawings!

---

## 💬 Support

For questions or issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review backend logs: `tail -f backend/logs/app.log`
3. Open an issue on GitHub
4. Contact the development team

---

**Happy Drawing! 🎨✨**

# Quick Start Guide

Get the Parametric Curve Drawing System up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Or copy from the example:

```bash
cp .env.example .env
# Then edit .env with your actual API key
```

### 3. Run the Server

Option A - Using the run script:
```bash
./run_server.sh
```

Option B - Direct command:
```bash
uvicorn backend.main:app --reload
```

The server will start at `http://localhost:8000`

### 4. Test the API

Open another terminal and try:

```bash
curl -X POST "http://localhost:8000/draw" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Draw a circle"}'
```

Or visit the interactive API docs at: `http://localhost:8000/docs`

### 5. Run Tests

```bash
python tests/test_sample_prompt.py
```

## Example Usage

### Simple Test

```python
from backend import pipeline

result = pipeline.run_pipeline("Draw a butterfly")
print(f"Score: {result['evaluation_score']}/10")
print(f"Image: {result['image_path']}")
```

### Interactive Mode

```bash
python tests/test_sample_prompt.py --interactive
```

Then enter prompts like:
- "Draw a heart"
- "Draw a flower with 5 petals"
- "Draw a spiral"

## Viewing Results

Generated images are saved in the `static/` directory. You can:

1. Open them directly from the file system
2. Access via API: `http://localhost:8000/static/filename.png`
3. Use the base64 data returned in the API response

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
→ Make sure your `.env` file exists and contains the key

### "Address already in use"
→ Change the port: `uvicorn backend.main:app --port 8001`

### "Module not found"
→ Install dependencies: `pip install -r requirements.txt`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at `http://localhost:8000/docs`
- Try the example prompts from `GET /examples`
- Modify the code in `backend/` to customize behavior

## Architecture at a Glance

```
Prompt → Claude (interpret) → Claude (generate equations) →
  Loop: Render → Evaluate → Refine → Final Image
```

## Example Prompts to Try

1. **Simple**: "Draw a circle"
2. **Medium**: "Draw a heart shape"
3. **Complex**: "Draw a butterfly with symmetric wings"
4. **Advanced**: "Draw a spiral galaxy"

---

**Need help?** Check the full [README.md](README.md) or open an issue!

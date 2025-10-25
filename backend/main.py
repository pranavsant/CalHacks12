"""
FastAPI Main Application - Entry point for the Parametric Curve Drawing System API.
"""

import os
import logging
import tempfile
from dotenv import load_dotenv

# Load environment variables FIRST before importing any backend modules
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from . import pipeline

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Parametric Curve Drawing System",
    description="Transform natural language prompts into mathematical parametric curves and rendered images",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Pydantic models for request/response
class DrawRequest(BaseModel):
    """Request model for text-based drawing."""
    prompt: str
    use_letta: Optional[bool] = False


class DrawResponse(BaseModel):
    """Response model for drawing results."""
    success: bool
    prompt: Optional[str] = None
    description: Optional[dict] = None
    curves: Optional[dict] = None
    iterations: Optional[int] = None
    evaluation_score: Optional[float] = None
    evaluation_feedback: Optional[str] = None
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    processing_time: Optional[float] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Parametric Curve Drawing System API")

    # Check for required API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.warning("ANTHROPIC_API_KEY not found - Claude API calls will fail")
    else:
        logger.info("Anthropic API key configured")

    vapi_key = os.getenv("VAPI_API_KEY")
    if not vapi_key:
        logger.info("VAPI_API_KEY not found - voice input will not work")
    else:
        logger.info("Vapi API key configured")

    letta_key = os.getenv("LETTA_API_KEY")
    if letta_key:
        logger.info("Letta API key configured")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down Parametric Curve Drawing System API")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Parametric Curve Drawing System",
        "version": "1.0.0",
        "description": "Transform natural language into parametric curves",
        "endpoints": {
            "POST /draw": "Create a drawing from text prompt",
            "POST /draw/audio": "Create a drawing from audio file",
            "GET /health": "Health check",
            "GET /static/{filename}": "Access generated images"
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check if required services are configured
    anthropic_ok = bool(os.getenv("ANTHROPIC_API_KEY"))

    return {
        "status": "healthy" if anthropic_ok else "degraded",
        "services": {
            "anthropic_claude": "configured" if anthropic_ok else "missing_api_key",
            "vapi_voice": "configured" if os.getenv("VAPI_API_KEY") else "not_configured",
            "letta_memory": "configured" if os.getenv("LETTA_API_KEY") else "not_configured"
        }
    }


@app.post("/draw", response_model=DrawResponse)
async def create_drawing(request: DrawRequest):
    """
    Create a parametric curve drawing from a text prompt.

    Args:
        request: DrawRequest with prompt text

    Returns:
        DrawResponse with curves, image, and metadata
    """
    logger.info(f"Received drawing request: '{request.prompt}'")

    try:
        # Validate prompt
        if not request.prompt or not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )

        # Run the pipeline
        result = pipeline.run_pipeline(
            prompt_text=request.prompt.strip(),
            use_letta=request.use_letta
        )

        # Return the result
        return DrawResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/draw/audio")
async def create_drawing_from_audio(
    audio: UploadFile = File(...),
    use_letta: Optional[bool] = Form(False)
):
    """
    Create a parametric curve drawing from an audio file.

    Args:
        audio: Audio file (WAV, MP3, etc.)
        use_letta: Whether to use Letta Cloud for memory

    Returns:
        JSON response with curves, image, and metadata
    """
    logger.info(f"Received audio drawing request: {audio.filename}")

    temp_audio_path = None

    try:
        # Validate file type
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Save uploaded file to temporary location
        suffix = os.path.splitext(audio.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name

        logger.info(f"Saved audio to temporary file: {temp_audio_path}")

        # Run the pipeline with audio
        result = pipeline.run_pipeline_from_audio(
            audio_path=temp_audio_path,
            use_letta=use_letta
        )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    finally:
        # Clean up temporary file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"Cleaned up temporary audio file: {temp_audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")


@app.get("/image/{filename}")
async def get_image(filename: str):
    """
    Get a generated image file.

    Args:
        filename: Name of the image file

    Returns:
        Image file
    """
    file_path = os.path.join(STATIC_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path, media_type="image/png")


@app.get("/examples")
async def get_examples():
    """
    Get example prompts that work well with the system.
    """
    return {
        "examples": [
            {
                "prompt": "Draw a circle",
                "complexity": 1,
                "description": "Simple geometric shape"
            },
            {
                "prompt": "Draw a heart shape",
                "complexity": 2,
                "description": "Classic symmetric heart"
            },
            {
                "prompt": "Draw a butterfly with symmetric wings",
                "complexity": 3,
                "description": "Butterfly with mirrored wing patterns"
            },
            {
                "prompt": "Draw a flower with 5 petals",
                "complexity": 3,
                "description": "Radial flower pattern"
            },
            {
                "prompt": "Draw a spiral galaxy",
                "complexity": 4,
                "description": "Logarithmic spiral pattern"
            },
            {
                "prompt": "Draw a complex Celtic knot",
                "complexity": 5,
                "description": "Intricate interwoven pattern"
            }
        ]
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for uncaught errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again."
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Run the server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

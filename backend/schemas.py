"""
Pydantic schemas for the Parametric Curve Drawing System.
Defines the data models for requests, responses, and internal data structures.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union


class CurveDef(BaseModel):
    """Definition of a parametric curve in absolute coordinates."""
    name: str
    x: str  # expression in t
    y: str  # expression in t
    t_min: float
    t_max: float
    color: Optional[str] = None  # existing metadata (absolute)


class AbsoluteCurves(BaseModel):
    """Collection of absolute parametric curves (legacy/backward compatibility)."""
    curves: List[CurveDef]


class PenSpec(BaseModel):
    """Pen specification for drawing a curve segment."""
    # color: hex or named color; "none" means pen up (no drawing, just move)
    color: str = Field(..., description='Use "none" to lift pen; otherwise hex color like "#FF4500"')


class RelativeCurveDef(BaseModel):
    """
    Definition of a parametric curve in relative coordinates.

    Each segment is expressed in the local frame of where the previous segment ended.
    The robot executes this relative to its current pose (x, y, theta) = (0, 0, 0).
    """
    name: str
    x_rel: str  # relative x expression in terms of t
    y_rel: str  # relative y expression in terms of t
    t_min: float
    t_max: float
    pen: PenSpec


class RelativeProgram(BaseModel):
    """
    A complete drawing program as a sequence of relative parametric segments.

    The robot executes each segment in order, with its local frame resetting
    to (0, 0, 0) at the end of each segment. The robot does not track global position.
    """
    segments: List[RelativeCurveDef]


class DrawResult(BaseModel):
    """
    Complete result from the drawing pipeline.

    Includes both the legacy absolute curves format and the new preferred
    relative_program format for robot execution.
    """
    success: bool
    prompt: str
    iterations: int
    evaluation_score: Optional[float] = None
    evaluation_feedback: Optional[str] = None

    # Legacy absolute structure (backward compatibility)
    description: Optional[Dict[str, Any]] = None
    curves: Optional[AbsoluteCurves] = None

    # NEW preferred structure for robot execution
    relative_program: Optional[RelativeProgram] = None

    # Visualization and metadata
    image_path: Optional[str] = None
    image_base64: Optional[str] = None
    processing_time: Optional[float] = None
    session_id: Optional[str] = None

    # Additional metadata
    notes: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None

"""
Test response schema validation.

Verifies that the DrawResult schema correctly validates responses
from the pipeline, including the new relative_program field.
"""

import pytest
from pydantic import ValidationError
from backend.app.schemas import (
    CurveDef,
    AbsoluteCurves,
    PenSpec,
    RelativeCurveDef,
    RelativeProgram,
    DrawResult
)


def test_curve_def_valid():
    """Test that CurveDef validates correctly."""
    curve = CurveDef(
        name="test_curve",
        x="cos(t)",
        y="sin(t)",
        t_min=0.0,
        t_max=6.28318531,
        color="#FF0000"
    )

    assert curve.name == "test_curve"
    assert curve.x == "cos(t)"
    assert curve.y == "sin(t)"
    assert curve.t_min == 0.0
    assert curve.t_max == 6.28318531
    assert curve.color == "#FF0000"


def test_curve_def_optional_color():
    """Test that CurveDef accepts None for color."""
    curve = CurveDef(
        name="test_curve",
        x="t",
        y="0",
        t_min=0.0,
        t_max=1.0
    )

    assert curve.color is None


def test_absolute_curves_valid():
    """Test that AbsoluteCurves validates correctly."""
    curves = AbsoluteCurves(
        curves=[
            CurveDef(name="c1", x="t", y="0", t_min=0, t_max=1, color="#FF0000"),
            CurveDef(name="c2", x="0", y="t", t_min=0, t_max=1, color="#00FF00")
        ]
    )

    assert len(curves.curves) == 2
    assert curves.curves[0].name == "c1"
    assert curves.curves[1].name == "c2"


def test_pen_spec_with_color():
    """Test that PenSpec normalizes colors."""
    from backend.app.color_utils import BLUE
    pen = PenSpec(color="#ABCDEF")
    # #ABCDEF (light blue) normalizes to blue
    assert pen.color == BLUE


def test_pen_spec_with_none():
    """Test that PenSpec validates with 'none' for pen up."""
    pen = PenSpec(color="none")
    assert pen.color == "none"


def test_relative_curve_def_valid():
    """Test that RelativeCurveDef validates and normalizes colors."""
    from backend.app.color_utils import BLACK
    rel_curve = RelativeCurveDef(
        name="rel_segment",
        x_rel="0.5 * t",
        y_rel="0.5 * t",
        t_min=0.0,
        t_max=1.0,
        pen=PenSpec(color="#FF4500")
    )

    assert rel_curve.name == "rel_segment"
    assert rel_curve.x_rel == "0.5 * t"
    assert rel_curve.y_rel == "0.5 * t"
    # #FF4500 (orange-red) normalizes to black
    assert rel_curve.pen.color == BLACK


def test_relative_program_valid():
    """Test that RelativeProgram validates correctly."""
    program = RelativeProgram(
        segments=[
            RelativeCurveDef(
                name="seg1",
                x_rel="t",
                y_rel="0",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#FF0000")
            ),
            RelativeCurveDef(
                name="seg2",
                x_rel="0",
                y_rel="t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#00FF00")
            )
        ]
    )

    assert len(program.segments) == 2
    assert program.segments[0].name == "seg1"
    assert program.segments[1].name == "seg2"


def test_draw_result_complete():
    """Test that DrawResult validates with all fields."""
    result = DrawResult(
        success=True,
        prompt="Draw a circle",
        iterations=2,
        evaluation_score=9.5,
        evaluation_feedback="Looks great!",
        description={"description": "A circle", "complexity": 2},
        curves=AbsoluteCurves(
            curves=[
                CurveDef(name="circle", x="cos(t)", y="sin(t)",
                        t_min=0, t_max=6.28, color="#FF0000")
            ]
        ),
        relative_program=RelativeProgram(
            segments=[
                RelativeCurveDef(
                    name="circle",
                    x_rel="cos(t)",
                    y_rel="sin(t)",
                    t_min=0.0,
                    t_max=6.28,
                    pen=PenSpec(color="#FF0000")
                )
            ]
        ),
        image_path="/path/to/image.png",
        image_base64="data:image/png;base64,ABC123",
        processing_time=5.25,
        session_id="abc-123",
        notes="Test note",
        stats={"stat1": 1, "stat2": 2}
    )

    assert result.success is True
    assert result.prompt == "Draw a circle"
    assert result.iterations == 2
    assert result.evaluation_score == 9.5
    assert result.relative_program is not None
    assert len(result.relative_program.segments) == 1


def test_draw_result_minimal():
    """Test that DrawResult validates with minimal required fields."""
    result = DrawResult(
        success=True,
        prompt="Test prompt",
        iterations=1
    )

    assert result.success is True
    assert result.prompt == "Test prompt"
    assert result.iterations == 1
    assert result.evaluation_score is None
    assert result.relative_program is None


def test_draw_result_with_error():
    """Test that DrawResult validates for error responses."""
    result = DrawResult(
        success=False,
        prompt="Failed prompt",
        iterations=0,
        error="Something went wrong"
    )

    assert result.success is False
    assert result.error == "Something went wrong"


def test_draw_result_serialization():
    """Test that DrawResult can be serialized to dict."""
    result = DrawResult(
        success=True,
        prompt="Test",
        iterations=1,
        relative_program=RelativeProgram(
            segments=[
                RelativeCurveDef(
                    name="seg",
                    x_rel="t",
                    y_rel="0",
                    t_min=0,
                    t_max=1,
                    pen=PenSpec(color="#000000")
                )
            ]
        )
    )

    result_dict = result.model_dump()

    assert result_dict['success'] is True
    assert result_dict['prompt'] == "Test"
    assert 'relative_program' in result_dict
    assert 'segments' in result_dict['relative_program']
    assert len(result_dict['relative_program']['segments']) == 1


def test_draw_result_from_pipeline_format():
    """Test that DrawResult can be created from pipeline output format."""
    # Simulate what the pipeline returns
    pipeline_output = {
        "success": True,
        "prompt": "Draw a butterfly",
        "description": {"description": "A butterfly", "complexity": 3},
        "curves": {
            "curves": [
                {"name": "wing", "x": "cos(t)", "y": "sin(t)",
                 "t_min": 0.0, "t_max": 6.28, "color": "#FF4500"}
            ]
        },
        "relative_program": {
            "segments": [
                {
                    "name": "wing",
                    "x_rel": "cos(t)",
                    "y_rel": "sin(t)",
                    "t_min": 0.0,
                    "t_max": 6.28,
                    "pen": {"color": "#FF4500"}
                }
            ]
        },
        "iterations": 2,
        "evaluation_score": 8.5,
        "evaluation_feedback": "Good",
        "image_path": "/static/output.png",
        "image_base64": "data:image/png;base64,XYZ",
        "processing_time": 10.5,
        "session_id": "sess-123"
    }

    # This should validate without error
    from backend.app.color_utils import BLACK
    result = DrawResult(**pipeline_output)

    assert result.success is True
    assert result.prompt == "Draw a butterfly"
    assert result.relative_program is not None
    assert len(result.relative_program.segments) == 1
    # #FF4500 (orange-red) normalizes to black
    assert result.relative_program.segments[0].pen.color == BLACK


def test_invalid_relative_curve_missing_field():
    """Test that RelativeCurveDef raises error for missing required field."""
    with pytest.raises(ValidationError):
        RelativeCurveDef(
            name="incomplete",
            x_rel="t",
            # Missing y_rel
            t_min=0.0,
            t_max=1.0,
            pen=PenSpec(color="#000000")
        )


def test_invalid_pen_spec_missing_color():
    """Test that PenSpec raises error for missing color."""
    with pytest.raises(ValidationError):
        PenSpec()  # Missing required 'color' field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

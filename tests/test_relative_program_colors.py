"""
Integration tests for relative program color normalization.

Verifies that the full pipeline produces relative programs with only
allowed colors (black, blue, or pen-up).
"""

import pytest
from backend.schemas import CurveDef, RelativeProgram, PenSpec
from backend.utils_relative import wrap_to_relative, compute_end_pose
from backend.color_utils import BLACK, BLUE, PEN_UP


class TestRelativeProgramColorIntegration:
    """Integration tests for color normalization in relative programs."""

    def test_wrap_to_relative_normalizes_colors(self):
        """Verify wrap_to_relative normalizes colors correctly."""
        # Create test curve with arbitrary color
        curve = CurveDef(
            name="test_curve",
            x="cos(t)",
            y="sin(t)",
            t_min=0.0,
            t_max=6.283185307179586,
            color="#FF4500"  # Orange-red
        )

        # Transform to relative
        prev_pose = (0.0, 0.0, 0.0)
        relative_seg = wrap_to_relative(prev_pose, curve)

        # Verify color is normalized (orange-red -> black)
        assert relative_seg.pen.color == BLACK

    def test_wrap_to_relative_with_blue_input(self):
        """Verify wrap_to_relative preserves blue colors."""
        curve = CurveDef(
            name="blue_curve",
            x="t",
            y="t*t",
            t_min=0.0,
            t_max=1.0,
            color="#4169E1"  # Royal blue
        )

        prev_pose = (0.0, 0.0, 0.0)
        relative_seg = wrap_to_relative(prev_pose, curve)

        # Verify color is normalized to blue
        assert relative_seg.pen.color == BLUE

    def test_wrap_to_relative_with_pen_up(self):
        """Verify wrap_to_relative preserves pen-up state."""
        curve = CurveDef(
            name="travel_segment",
            x="t",
            y="0",
            t_min=0.0,
            t_max=1.0,
            color=None
        )

        prev_pose = (1.0, 1.0, 0.0)
        relative_seg = wrap_to_relative(prev_pose, curve, default_color="none")

        # Verify pen is up
        assert relative_seg.pen.color == PEN_UP

    def test_wrap_to_relative_default_color(self):
        """Verify wrap_to_relative uses default color when curve has none."""
        curve = CurveDef(
            name="no_color_curve",
            x="t",
            y="t",
            t_min=0.0,
            t_max=1.0,
            color=None
        )

        prev_pose = (0.0, 0.0, 0.0)
        relative_seg = wrap_to_relative(prev_pose, curve)

        # Should default to black
        assert relative_seg.pen.color == BLACK

    def test_multiple_curves_all_normalized(self):
        """Verify that multiple curves with different colors are all normalized."""
        test_curves = [
            CurveDef(name="red", x="t", y="t", t_min=0.0, t_max=1.0, color="#FF0000"),
            CurveDef(name="green", x="t", y="t", t_min=0.0, t_max=1.0, color="#00FF00"),
            CurveDef(name="blue", x="t", y="t", t_min=0.0, t_max=1.0, color="#0000FF"),
            CurveDef(name="orange", x="t", y="t", t_min=0.0, t_max=1.0, color="#FFA500"),
            CurveDef(name="purple", x="t", y="t", t_min=0.0, t_max=1.0, color="#800080"),
            CurveDef(name="cyan", x="t", y="t", t_min=0.0, t_max=1.0, color="#00FFFF"),
        ]

        allowed_colors = {BLACK, BLUE, PEN_UP}
        relative_segments = []

        current_pose = (0.0, 0.0, 0.0)
        for curve in test_curves:
            rel_seg = wrap_to_relative(current_pose, curve)
            relative_segments.append(rel_seg)

            # Verify color is allowed
            assert rel_seg.pen.color in allowed_colors, \
                f"Curve '{curve.name}' produced invalid color: {rel_seg.pen.color}"

            # Update pose for next iteration
            current_pose = compute_end_pose(curve)

        # Build RelativeProgram and verify
        program = RelativeProgram(segments=relative_segments)
        for seg in program.segments:
            assert seg.pen.color in allowed_colors


class TestPipelineColorNormalization:
    """Test color normalization in the full pipeline."""

    def test_build_relative_program_from_dict(self):
        """Test building relative program from curve dict with various colors."""
        from backend.pipeline import Pipeline

        # Create mock curves dict
        curves_dict = {
            "curves": [
                {
                    "name": "curve1",
                    "x": "cos(t)",
                    "y": "sin(t)",
                    "t_min": 0.0,
                    "t_max": 6.283185307179586,
                    "color": "#FF0000"  # Red
                },
                {
                    "name": "curve2",
                    "x": "t",
                    "y": "t*t",
                    "t_min": 0.0,
                    "t_max": 1.0,
                    "color": "#4169E1"  # Royal blue
                },
                {
                    "name": "curve3",
                    "x": "2 + t",
                    "y": "t",
                    "t_min": 0.0,
                    "t_max": 1.0,
                    "color": "#00FF00"  # Green
                },
            ]
        }

        # Build relative program
        pipeline = Pipeline(use_letta=False)
        relative_program = pipeline._build_relative_program(curves_dict)

        # Verify all colors are normalized
        allowed_colors = {BLACK, BLUE, PEN_UP}
        for seg in relative_program.segments:
            assert seg.pen.color in allowed_colors, \
                f"Segment '{seg.name}' has invalid color: {seg.pen.color}"

        # Verify we have the expected number of segments
        # (may include travel segments if curves are disconnected)
        assert len(relative_program.segments) >= 3

    def test_travel_segments_have_pen_up(self):
        """Verify that auto-inserted travel segments have pen up."""
        from backend.pipeline import Pipeline

        # Create disconnected curves (will require travel segments)
        curves_dict = {
            "curves": [
                {
                    "name": "curve1",
                    "x": "t",
                    "y": "t",
                    "t_min": 0.0,
                    "t_max": 1.0,
                    "color": "#FF0000"
                },
                {
                    "name": "curve2",
                    "x": "5 + t",  # Starts at (5, 5), disconnected from curve1 end
                    "y": "5 + t",
                    "t_min": 0.0,
                    "t_max": 1.0,
                    "color": "#0000FF"
                },
            ]
        }

        pipeline = Pipeline(use_letta=False)
        relative_program = pipeline._build_relative_program(curves_dict)

        # Should have at least 3 segments: curve1, travel, curve2
        assert len(relative_program.segments) >= 3

        # Find travel segments (name contains "travel")
        travel_segments = [s for s in relative_program.segments if "travel" in s.name]

        # Verify all travel segments have pen up
        for seg in travel_segments:
            assert seg.pen.color == PEN_UP, \
                f"Travel segment '{seg.name}' should have pen up, got: {seg.pen.color}"

    def test_serialization_preserves_normalized_colors(self):
        """Verify that serialization/deserialization preserves normalized colors."""
        from backend.schemas import RelativeCurveDef, PenSpec, RelativeProgram

        # Create program with arbitrary colors
        segments = [
            RelativeCurveDef(
                name="seg1",
                x_rel="t",
                y_rel="t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#FF0000")  # Will normalize to black
            ),
            RelativeCurveDef(
                name="seg2",
                x_rel="t",
                y_rel="t*t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#0080FF")  # Will normalize to blue
            ),
        ]

        program = RelativeProgram(segments=segments)

        # Serialize
        program_dict = program.model_dump()

        # Verify serialized data has normalized colors
        assert program_dict["segments"][0]["pen"]["color"] == BLACK
        assert program_dict["segments"][1]["pen"]["color"] == BLUE

        # Deserialize
        program2 = RelativeProgram(**program_dict)

        # Verify deserialized program still has normalized colors
        assert program2.segments[0].pen.color == BLACK
        assert program2.segments[1].pen.color == BLUE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

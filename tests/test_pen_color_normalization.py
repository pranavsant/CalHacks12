"""
Tests for pen color normalization.

Verifies that all colors are correctly normalized to black, blue, or pen-up.
"""

import pytest
from backend.color_utils import normalize_draw_color, BLACK, BLUE, PEN_UP


class TestColorNormalization:
    """Test suite for color normalization utilities."""

    def test_normalize_pen_up(self):
        """Verify that 'none' is preserved as pen-up."""
        assert normalize_draw_color("none") == PEN_UP
        assert normalize_draw_color("NONE") == PEN_UP
        assert normalize_draw_color("  none  ") == PEN_UP

    def test_normalize_exact_black(self):
        """Verify that exact black stays black."""
        assert normalize_draw_color("#000000") == BLACK
        assert normalize_draw_color("black") == BLACK

    def test_normalize_exact_blue(self):
        """Verify that exact blue stays blue."""
        assert normalize_draw_color("#0000FF") == BLUE
        assert normalize_draw_color("blue") == BLUE

    def test_normalize_colors_closer_to_black(self):
        """Verify that colors closer to black are mapped to black."""
        # Dark gray
        assert normalize_draw_color("#010101") == BLACK
        # Dark red
        assert normalize_draw_color("#330000") == BLACK
        # Olive (dark yellow-green)
        assert normalize_draw_color("#808000") == BLACK
        # Red
        assert normalize_draw_color("#FF0000") == BLACK
        # Green
        assert normalize_draw_color("#00FF00") == BLACK
        # Orange-red (example from docs)
        assert normalize_draw_color("#FF4500") == BLACK

    def test_normalize_colors_closer_to_blue(self):
        """Verify that colors closer to blue are mapped to blue."""
        # Light blue
        assert normalize_draw_color("#0010F0") == BLUE
        # Cyan
        assert normalize_draw_color("#00FFFF") == BLUE
        # Royal blue
        assert normalize_draw_color("#4169E1") == BLUE
        # Violet/purple (closer to blue than black)
        assert normalize_draw_color("#8000FF") == BLUE

    def test_normalize_named_colors(self):
        """Verify that common named colors are recognized."""
        assert normalize_draw_color("red") == BLACK
        assert normalize_draw_color("green") == BLACK
        assert normalize_draw_color("yellow") == BLACK
        assert normalize_draw_color("cyan") == BLUE
        assert normalize_draw_color("magenta") == BLUE  # (255,0,255) closer to blue than black

    def test_normalize_invalid_defaults_to_black(self):
        """Verify that invalid colors default to black."""
        assert normalize_draw_color("not-a-color") == BLACK
        assert normalize_draw_color(None) == BLACK
        assert normalize_draw_color("") == BLACK
        assert normalize_draw_color("#GGGGGG") == BLACK  # Invalid hex

    def test_normalize_case_insensitive(self):
        """Verify that color parsing is case-insensitive."""
        assert normalize_draw_color("#000000") == BLACK
        assert normalize_draw_color("#0000ff") == BLUE
        assert normalize_draw_color("#0000FF") == BLUE
        assert normalize_draw_color("BLUE") == BLUE
        assert normalize_draw_color("Blue") == BLUE
        assert normalize_draw_color("BLACK") == BLACK


class TestPenSpecValidation:
    """Test suite for PenSpec schema validation."""

    def test_penspec_normalizes_colors(self):
        """Verify that PenSpec validator normalizes colors."""
        from backend.schemas import PenSpec

        # Test exact values
        pen = PenSpec(color="none")
        assert pen.color == PEN_UP

        pen = PenSpec(color="#000000")
        assert pen.color == BLACK

        pen = PenSpec(color="#0000FF")
        assert pen.color == BLUE

    def test_penspec_normalizes_arbitrary_colors(self):
        """Verify that PenSpec normalizes arbitrary colors."""
        from backend.schemas import PenSpec

        # Red -> black
        pen = PenSpec(color="#FF0000")
        assert pen.color == BLACK

        # Orange -> black
        pen = PenSpec(color="#FF4500")
        assert pen.color == BLACK

        # Cyan -> blue
        pen = PenSpec(color="#00FFFF")
        assert pen.color == BLUE

        # Royal blue -> blue
        pen = PenSpec(color="#4169E1")
        assert pen.color == BLUE

    def test_penspec_handles_none_input(self):
        """Verify that PenSpec handles None input by defaulting to black."""
        from backend.schemas import PenSpec

        pen = PenSpec(color=None)
        assert pen.color == BLACK

    def test_penspec_json_schema_validation(self):
        """Verify that PenSpec can be serialized and deserialized."""
        from backend.schemas import PenSpec

        # Create PenSpec with arbitrary color
        pen = PenSpec(color="#FF4500")
        assert pen.color == BLACK

        # Serialize
        pen_dict = pen.model_dump()
        assert pen_dict["color"] == BLACK

        # Deserialize
        pen2 = PenSpec(**pen_dict)
        assert pen2.color == BLACK


class TestRelativeProgramColorNormalization:
    """Test suite for relative program color normalization."""

    def test_relative_program_normalizes_segment_colors(self):
        """Verify that RelativeProgram segments have normalized colors."""
        from backend.schemas import RelativeCurveDef, PenSpec, RelativeProgram

        # Create segments with various colors
        segments = [
            RelativeCurveDef(
                name="seg1",
                x_rel="t",
                y_rel="t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#FF0000")  # Red -> black
            ),
            RelativeCurveDef(
                name="seg2",
                x_rel="t",
                y_rel="t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="#4169E1")  # Royal blue -> blue
            ),
            RelativeCurveDef(
                name="travel",
                x_rel="t",
                y_rel="0",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color="none")  # Pen up
            ),
        ]

        program = RelativeProgram(segments=segments)

        # Verify all colors are normalized
        assert program.segments[0].pen.color == BLACK
        assert program.segments[1].pen.color == BLUE
        assert program.segments[2].pen.color == PEN_UP

    def test_only_allowed_colors_in_program(self):
        """Verify that only allowed colors appear in relative programs."""
        from backend.schemas import RelativeCurveDef, PenSpec, RelativeProgram

        allowed_colors = {BLACK, BLUE, PEN_UP}

        # Create segments with many different colors
        test_colors = ["#FF0000", "#00FF00", "#FFFF00", "#FF00FF", "#00FFFF",
                       "#FFA500", "#800080", "red", "green", "blue", "none"]

        segments = [
            RelativeCurveDef(
                name=f"seg_{i}",
                x_rel="t",
                y_rel="t",
                t_min=0.0,
                t_max=1.0,
                pen=PenSpec(color=color)
            )
            for i, color in enumerate(test_colors)
        ]

        program = RelativeProgram(segments=segments)

        # Verify ALL segments have only allowed colors
        for seg in program.segments:
            assert seg.pen.color in allowed_colors, \
                f"Segment '{seg.name}' has invalid color: {seg.pen.color}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

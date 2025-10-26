"""
Simple integration test for robot export functionality.
Tests the export logic without requiring full API server.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_export_directory_structure():
    """Test that exports directory can be created."""
    from backend.pipeline import Path as PipelinePath

    exports_dir = PipelinePath("exports")
    exports_dir.mkdir(parents=True, exist_ok=True)

    assert exports_dir.exists()
    assert exports_dir.is_dir()
    print("✓ Exports directory structure OK")


def test_uuid_generation():
    """Test that UUID generation works correctly."""
    import uuid

    run_id = uuid.uuid4().hex

    assert isinstance(run_id, str)
    assert len(run_id) == 32
    assert all(c in "0123456789abcdef" for c in run_id)
    print(f"✓ UUID generation OK: {run_id[:8]}...")


def test_pydantic_compatibility():
    """Test that Pydantic models support both v1 and v2."""
    from backend.schemas import RelativeProgram, RelativeCurveDef, PenSpec

    # Create a simple program
    segment = RelativeCurveDef(
        name="test",
        x_rel="t",
        y_rel="0",
        t_min=0.0,
        t_max=1.0,
        pen=PenSpec(color="#FF0000")
    )

    program = RelativeProgram(segments=[segment])

    # Test both methods
    if hasattr(program, "model_dump"):
        data = program.model_dump()
        print("✓ Pydantic v2 (model_dump) supported")
    elif hasattr(program, "dict"):
        data = program.dict()
        print("✓ Pydantic v1 (dict) supported")
    else:
        raise AssertionError("Neither model_dump nor dict available")

    assert "segments" in data
    assert len(data["segments"]) == 1
    assert data["segments"][0]["name"] == "test"


def test_json_serialization():
    """Test that JSON serialization works for export payloads."""
    import tempfile

    payload = {
        "run_id": "test123",
        "prompt": "Test prompt",
        "relative_program": {
            "segments": [
                {
                    "name": "seg1",
                    "x_rel": "t",
                    "y_rel": "0",
                    "t_min": 0.0,
                    "t_max": 1.0,
                    "pen": {"color": "#000000"}
                }
            ]
        }
    }

    # Test atomic write pattern
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tf:
        json.dump(payload, tf, indent=2)
        tmp_name = tf.name

    # Read back
    with open(tmp_name, "r") as f:
        loaded = json.load(f)

    assert loaded["run_id"] == "test123"
    assert loaded["prompt"] == "Test prompt"
    assert "segments" in loaded["relative_program"]

    # Clean up
    os.remove(tmp_name)

    print("✓ JSON serialization and atomic write OK")


def test_path_sanitization():
    """Test that path sanitization logic works correctly."""

    def is_valid_run_id(run_id: str) -> bool:
        """Mimics the validation in the endpoint."""
        if not run_id:
            return False
        return all(ch in "0123456789abcdefABCDEF-" for ch in run_id)

    # Valid IDs
    assert is_valid_run_id("abc123def456")
    assert is_valid_run_id("ABCDEF0123456789")
    assert is_valid_run_id("abc-def-012-345")

    # Invalid IDs (should be rejected)
    assert not is_valid_run_id("../etc/passwd")
    assert not is_valid_run_id("test@domain.com")
    assert not is_valid_run_id("test id")
    assert not is_valid_run_id("test/path")
    assert not is_valid_run_id("")

    print("✓ Path sanitization logic OK")


if __name__ == "__main__":
    print("Running simple integration tests...\n")

    try:
        test_export_directory_structure()
        test_uuid_generation()
        test_pydantic_compatibility()
        test_json_serialization()
        test_path_sanitization()

        print("\n✅ All simple integration tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

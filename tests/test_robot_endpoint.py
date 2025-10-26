"""
Test robot endpoint export and fetch functionality.

Verifies that:
1. Drawing requests create durable exports in exports/ directory
2. The draw response includes run_id and export_path in stats
3. GET /robot/{run_id} endpoint returns the exported program
4. Invalid run_ids are handled correctly
"""

import json
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


# Import the FastAPI app
from backend.app.main import app

# Create test client
client = TestClient(app)


def test_draw_creates_export_file():
    """Test that POST /draw creates a durable export file."""
    # Send a simple draw request
    response = client.post("/draw", json={"prompt": "Draw a circle"})

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["success"] is True
    assert "stats" in data
    assert "run_id" in data["stats"]
    assert "export_path" in data["stats"]

    run_id = data["stats"]["run_id"]
    export_path = data["stats"]["export_path"]

    # Verify file exists
    assert os.path.exists(export_path)
    assert export_path.startswith("exports/relative_program_")
    assert export_path.endswith(".json")

    # Verify file contains valid JSON
    with open(export_path, "r") as f:
        payload = json.load(f)

    assert payload["run_id"] == run_id
    assert "relative_program" in payload
    assert "prompt" in payload
    assert payload["prompt"] == "Draw a circle"

    # Clean up
    try:
        os.remove(export_path)
    except:
        pass


def test_robot_endpoint_fetch():
    """Test that GET /robot/{run_id} returns the correct program."""
    # First, create a drawing
    response = client.post("/draw", json={"prompt": "Draw a heart shape"})
    assert response.status_code == 200
    data = response.json()

    run_id = data["stats"]["run_id"]

    # Now fetch from robot endpoint
    robot_response = client.get(f"/robot/{run_id}")

    assert robot_response.status_code == 200
    robot_data = robot_response.json()

    # Verify structure
    assert robot_data["run_id"] == run_id
    assert "relative_program" in robot_data
    assert "segments" in robot_data["relative_program"]
    assert isinstance(robot_data["relative_program"]["segments"], list)
    assert len(robot_data["relative_program"]["segments"]) > 0

    # Verify each segment has required fields
    for segment in robot_data["relative_program"]["segments"]:
        assert "name" in segment
        assert "x_rel" in segment
        assert "y_rel" in segment
        assert "t_min" in segment
        assert "t_max" in segment
        assert "pen" in segment
        assert "color" in segment["pen"]

    # Clean up
    try:
        export_path = data["stats"]["export_path"]
        os.remove(export_path)
    except:
        pass


def test_robot_endpoint_invalid_run_id():
    """Test that invalid run_ids are rejected."""
    # Test with directory traversal attempt
    response = client.get("/robot/../etc/passwd")
    assert response.status_code == 400
    assert "Invalid run_id format" in response.json()["detail"]

    # Test with special characters
    response = client.get("/robot/invalid@id")
    assert response.status_code == 400

    # Test with spaces
    response = client.get("/robot/invalid id")
    assert response.status_code == 400


def test_robot_endpoint_not_found():
    """Test that non-existent run_ids return 404."""
    # Use a valid format but non-existent ID
    fake_run_id = "0" * 32  # Valid hex format but doesn't exist

    response = client.get(f"/robot/{fake_run_id}")
    assert response.status_code == 404
    assert "Run not found" in response.json()["detail"]


def test_robot_endpoint_cache_headers():
    """Test that cache headers are set correctly."""
    # Create a drawing
    response = client.post("/draw", json={"prompt": "Draw a star"})
    assert response.status_code == 200
    run_id = response.json()["stats"]["run_id"]

    # Fetch from robot endpoint
    robot_response = client.get(f"/robot/{run_id}")
    assert robot_response.status_code == 200

    # Verify cache headers
    assert "cache-control" in robot_response.headers
    assert "max-age=5" in robot_response.headers["cache-control"].lower()

    # Clean up
    try:
        export_path = response.json()["stats"]["export_path"]
        os.remove(export_path)
    except:
        pass


def test_export_directory_created():
    """Test that exports directory is created if it doesn't exist."""
    # Remove exports directory if it exists
    exports_dir = Path("exports")
    if exports_dir.exists():
        # Don't remove, but verify it exists
        assert exports_dir.is_dir()
    else:
        # Create a drawing to trigger directory creation
        response = client.post("/draw", json={"prompt": "Draw a triangle"})
        assert response.status_code == 200

        # Verify directory was created
        assert exports_dir.exists()
        assert exports_dir.is_dir()

        # Clean up
        try:
            export_path = response.json()["stats"]["export_path"]
            os.remove(export_path)
        except:
            pass


def test_relative_program_segments_structure():
    """Test that relative program segments have correct structure."""
    response = client.post("/draw", json={"prompt": "Draw a simple curve"})
    assert response.status_code == 200
    data = response.json()

    run_id = data["stats"]["run_id"]

    # Fetch from robot endpoint
    robot_response = client.get(f"/robot/{run_id}")
    assert robot_response.status_code == 200
    robot_data = robot_response.json()

    # Verify relative_program structure
    rel_prog = robot_data["relative_program"]
    assert "segments" in rel_prog

    # Each segment should have the relative transformation applied
    for segment in rel_prog["segments"]:
        # Check that x_rel and y_rel are strings (expressions)
        assert isinstance(segment["x_rel"], str)
        assert isinstance(segment["y_rel"], str)

        # Check that t_min < t_max
        assert segment["t_min"] < segment["t_max"]

        # Check pen color format (should be hex color or "none")
        color = segment["pen"]["color"]
        assert isinstance(color, str)
        if color.lower() != "none":
            # Should be a valid color (hex or named)
            assert len(color) > 0

    # Clean up
    try:
        export_path = data["stats"]["export_path"]
        os.remove(export_path)
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

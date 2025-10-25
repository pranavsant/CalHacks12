"""
Claude API Client - Handles all interactions with Anthropic's Claude API.
This module provides functions for prompt interpretation, parametric equation generation,
and equation refinement based on feedback.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import anthropic

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not found in environment variables")

# Use the latest Claude Sonnet 4.5 model
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


def get_client() -> anthropic.Anthropic:
    """Get or create an Anthropic client instance."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def interpret_prompt(prompt_text: str) -> Dict[str, Any]:
    """
    Interpret the user's drawing prompt and extract structured information.

    Args:
        prompt_text: The natural language description of what to draw

    Returns:
        A dictionary containing:
        - description: detailed description of the object
        - components: list of visual components to draw
        - symmetry: type of symmetry (if any)
        - complexity: complexity rating (1-5)
    """
    logger.info(f"Interpreting prompt: {prompt_text}")

    client = get_client()

    system_message = """You are a visual interpreter AI. The user will describe an object to draw.
You will output a JSON describing the object's visual components, geometry, and complexity.
Do not output any extra text, only valid JSON.

The JSON should have this structure:
{
  "description": "detailed description of the object",
  "components": ["list", "of", "visual", "components"],
  "symmetry": "type of symmetry (e.g., 'vertical', 'horizontal', 'radial', 'none')",
  "complexity": 3
}

The complexity should be rated 1-5, where:
1 = very simple (circle, line)
2 = simple (heart, star)
3 = moderate (butterfly, flower)
4 = complex (detailed animal, building)
5 = very complex (intricate patterns, many components)
"""

    user_message = f"User prompt: {prompt_text}\n\nProvide the structured JSON interpretation of this drawing request."

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            temperature=0,
            system=system_message,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        # Extract the text content from the response
        content = response.content[0].text
        logger.info(f"Claude interpretation response: {content}")

        # Parse the JSON response
        interpretation = json.loads(content)

        # Validate required fields
        required_fields = ["description", "components", "symmetry", "complexity"]
        for field in required_fields:
            if field not in interpretation:
                raise ValueError(f"Missing required field: {field}")

        return interpretation

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude: {e}")
        logger.error(f"Response was: {content}")
        # Return a fallback interpretation
        return {
            "description": prompt_text,
            "components": ["shape"],
            "symmetry": "none",
            "complexity": 3
        }
    except Exception as e:
        logger.error(f"Error in interpret_prompt: {e}")
        raise


def generate_parametric_equations(description: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate parametric equations based on the interpreted description.

    Args:
        description: The structured description from interpret_prompt

    Returns:
        A dictionary containing:
        - curves: list of curve definitions with x(t), y(t), t_min, t_max, color, name
    """
    logger.info(f"Generating parametric equations for: {description['description']}")

    client = get_client()

    system_message = """You are a mathematical curve generator AI. Given a description of an object,
you produce parametric equations that will draw the object when plotted.

Output ONLY valid JSON in this exact format:
{
  "curves": [
    {
      "name": "descriptive_name",
      "x": "mathematical expression in terms of t",
      "y": "mathematical expression in terms of t",
      "t_min": starting_value,
      "t_max": ending_value,
      "color": "#HEXCOLOR"
    }
  ]
}

Rules for expressions:
- Use only these functions: sin, cos, tan, sqrt, exp, abs, log (natural log)
- Use standard operators: +, -, *, /, **
- The parameter is always 't'
- Use pi for π (it will be available as a constant)
- Example expressions: "cos(t)", "2*sin(3*t)", "t**2", "sqrt(abs(t))"

For symmetry:
- Vertical symmetry: create mirrored curves with x → -x
- Horizontal symmetry: create mirrored curves with y → -y
- Radial symmetry: use multiple curves at different angles

Choose appropriate colors (hex codes) for different components.
Use t ranges that create complete, smooth curves (typically 0 to 2*pi for periodic shapes).
"""

    # Create a detailed prompt
    components_str = ", ".join(description["components"])
    user_message = f"""Description: {description['description']}

Components to draw: {components_str}
Symmetry type: {description['symmetry']}
Complexity level: {description['complexity']}/5

Generate parametric equations that will create this drawing. Each component should be a separate curve.
For complexity {description['complexity']}, use an appropriate level of detail.

Output only the JSON, no other text."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            temperature=0.2,  # Slight temperature for creativity in curve generation
            system=system_message,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        content = response.content[0].text
        logger.info(f"Claude equation generation response: {content}")

        # Parse the JSON response
        equations = json.loads(content)

        # Validate the structure
        if "curves" not in equations or not isinstance(equations["curves"], list):
            raise ValueError("Response must contain a 'curves' array")

        # Validate each curve
        for i, curve in enumerate(equations["curves"]):
            required = ["name", "x", "y", "t_min", "t_max", "color"]
            for field in required:
                if field not in curve:
                    raise ValueError(f"Curve {i} missing required field: {field}")

        logger.info(f"Successfully generated {len(equations['curves'])} curves")
        return equations

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude: {e}")
        logger.error(f"Response was: {content}")
        # Return a fallback simple circle
        return {
            "curves": [
                {
                    "name": "simple_shape",
                    "x": "cos(t)",
                    "y": "sin(t)",
                    "t_min": 0,
                    "t_max": 6.283185307179586,  # 2*pi
                    "color": "#4169E1"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error in generate_parametric_equations: {e}")
        raise


def refine_equations(current_equations: Dict[str, Any], feedback: str) -> Dict[str, Any]:
    """
    Refine parametric equations based on evaluation feedback.

    Args:
        current_equations: The current curve definitions
        feedback: Feedback from the evaluator on how to improve

    Returns:
        Updated curve definitions in the same format
    """
    logger.info(f"Refining equations based on feedback: {feedback}")

    client = get_client()

    system_message = """You are an AI assistant that modifies parametric equations based on feedback.
The feedback will tell you how the drawn image differs from the desired outcome.
Adjust the equations accordingly.

Output ONLY valid JSON in the exact same format as the input:
{
  "curves": [
    {
      "name": "descriptive_name",
      "x": "mathematical expression in terms of t",
      "y": "mathematical expression in terms of t",
      "t_min": starting_value,
      "t_max": ending_value,
      "color": "#HEXCOLOR"
    }
  ]
}

Rules:
- Maintain the same structure and number of curves (unless feedback asks to add/remove)
- Use only these functions: sin, cos, tan, sqrt, exp, abs, log
- Keep expressions valid and mathematically sound
- Make targeted adjustments based on the specific feedback
"""

    # Format current equations as a clean JSON string
    current_json = json.dumps(current_equations, indent=2)

    user_message = f"""Current parametric equations:
{current_json}

Feedback: {feedback}

Please provide the refined equations that address this feedback.
Output only the JSON, no other text."""

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1500,
            temperature=0.1,  # Low temperature for precise modifications
            system=system_message,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        content = response.content[0].text
        logger.info(f"Claude refinement response: {content}")

        # Parse the JSON response
        refined_equations = json.loads(content)

        # Validate the structure
        if "curves" not in refined_equations or not isinstance(refined_equations["curves"], list):
            raise ValueError("Response must contain a 'curves' array")

        logger.info(f"Successfully refined {len(refined_equations['curves'])} curves")
        return refined_equations

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Claude: {e}")
        logger.error(f"Response was: {content}")
        # Return the original equations unchanged
        return current_equations
    except Exception as e:
        logger.error(f"Error in refine_equations: {e}")
        # Return the original equations unchanged
        return current_equations

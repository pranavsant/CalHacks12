"""
Example client script demonstrating how to use the Parametric Curve Drawing System API.
"""

import requests
import json
import base64
from pathlib import Path


def save_base64_image(base64_string: str, output_path: str) -> None:
    """Save a base64-encoded image to a file."""
    # Remove the data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    # Decode and save
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)


def create_drawing(prompt: str, api_url: str = "http://localhost:8000") -> dict:
    """
    Create a parametric curve drawing from a text prompt.

    Args:
        prompt: Description of what to draw
        api_url: Base URL of the API

    Returns:
        Response dictionary from the API
    """
    print(f"\n{'='*60}")
    print(f"Creating drawing: '{prompt}'")
    print('='*60)

    # Make the API request
    response = requests.post(
        f"{api_url}/draw",
        json={"prompt": prompt, "use_letta": False},
        timeout=60  # Allow up to 60 seconds for processing
    )

    if response.status_code == 200:
        result = response.json()

        if result.get("success"):
            print(f"✅ Success!")
            print(f"   Processing time: {result['processing_time']}s")
            print(f"   Iterations: {result['iterations']}")
            print(f"   Final score: {result['evaluation_score']}/10")
            print(f"   Curves generated: {len(result['curves']['curves'])}")

            # Print curve details
            print(f"\n   Parametric Equations:")
            for i, curve in enumerate(result['curves']['curves'], 1):
                print(f"   {i}. {curve['name']}")
                print(f"      x(t) = {curve['x']}")
                print(f"      y(t) = {curve['y']}")
                print(f"      t ∈ [{curve['t_min']:.2f}, {curve['t_max']:.2f}]")

            # Save the image
            if result.get('image_base64'):
                output_path = f"example_output_{result['session_id']}.png"
                save_base64_image(result['image_base64'], output_path)
                print(f"\n   📸 Image saved to: {output_path}")

            return result
        else:
            print(f"❌ Failed: {result.get('error')}")
            return result
    else:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")
        return {"success": False, "error": response.text}


def get_examples(api_url: str = "http://localhost:8000") -> list:
    """Get example prompts from the API."""
    response = requests.get(f"{api_url}/examples")
    if response.status_code == 200:
        return response.json()["examples"]
    return []


def check_health(api_url: str = "http://localhost:8000") -> dict:
    """Check the health status of the API."""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"status": "unreachable", "error": str(e)}


def main():
    """Main function demonstrating API usage."""
    API_URL = "http://localhost:8000"

    print("\n" + "="*60)
    print("  Parametric Curve Drawing System - Example Client")
    print("="*60)

    # Check health
    print("\nChecking API health...")
    health = check_health(API_URL)
    print(f"Status: {health.get('status')}")

    if health.get('status') != 'healthy':
        print("\n⚠️  Warning: API is not fully healthy")
        if 'services' in health:
            print("Services:")
            for service, status in health['services'].items():
                print(f"  - {service}: {status}")

    # Get and display examples
    print("\nFetching example prompts...")
    examples = get_examples(API_URL)

    if examples:
        print("\nAvailable examples:")
        for i, example in enumerate(examples, 1):
            print(f"{i}. {example['prompt']} (complexity: {example['complexity']}/5)")

    # Try a few examples
    test_prompts = [
        "Draw a circle",
        "Draw a heart shape",
        "Draw a butterfly with symmetric wings"
    ]

    print("\n" + "="*60)
    print("Running example drawings...")
    print("="*60)

    results = []
    for prompt in test_prompts:
        try:
            result = create_drawing(prompt, API_URL)
            results.append((prompt, result.get("success", False)))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((prompt, False))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for prompt, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {prompt}")

    print("\n✨ Done! Check the generated PNG files in the current directory.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

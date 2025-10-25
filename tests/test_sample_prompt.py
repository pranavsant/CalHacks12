"""
Test script for the Parametric Curve Drawing System.
This script runs the pipeline with sample prompts to verify functionality.
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import pipeline


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_prompt(prompt_text, test_name):
    """
    Test the pipeline with a given prompt.

    Args:
        prompt_text: The prompt to test
        test_name: Name of the test for logging
    """
    print_section(f"TEST: {test_name}")
    print(f"Prompt: '{prompt_text}'")
    print()

    try:
        result = pipeline.run_pipeline(prompt_text)

        if result.get("success"):
            print("\n✅ TEST PASSED")
            print(f"   Processing Time: {result['processing_time']}s")
            print(f"   Iterations: {result['iterations']}")
            print(f"   Final Score: {result['evaluation_score']}/10")
            print(f"   Image: {result['image_path']}")
            print(f"   Number of Curves: {len(result['curves']['curves'])}")

            # Print curve details
            print("\n   Curves Generated:")
            for i, curve in enumerate(result['curves']['curves'], 1):
                print(f"     {i}. {curve['name']}")
                print(f"        x(t) = {curve['x']}")
                print(f"        y(t) = {curve['y']}")
                print(f"        t ∈ [{curve['t_min']}, {curve['t_max']}]")
                print(f"        color = {curve['color']}")

            return True
        else:
            print(f"\n❌ TEST FAILED")
            print(f"   Error: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION")
        print(f"   Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run a suite of test prompts."""
    print_section("PARAMETRIC CURVE DRAWING SYSTEM - TEST SUITE")
    print("This script tests the pipeline with various prompts")
    print()

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: ANTHROPIC_API_KEY not found in environment")
        print("   The tests will likely fail without a valid API key")
        print("   Set the API key in a .env file or environment variable")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            return

    # Test cases with increasing complexity
    test_cases = [
        ("Draw a circle", "Simple Circle"),
        ("Draw a heart shape", "Heart Shape"),
        ("Draw a butterfly with symmetric wings", "Butterfly"),
        ("Draw a flower with 5 petals", "Five-petal Flower"),
        ("Draw a star with 5 points", "Five-pointed Star"),
    ]

    results = []
    for prompt, name in test_cases:
        success = test_prompt(prompt, name)
        results.append((name, success))

    # Print summary
    print_section("TEST SUMMARY")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(1 for _, success in results if success)}")
    print(f"Failed: {sum(1 for _, success in results if not success)}")
    print()

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {name}")

    print()


def interactive_mode():
    """Run the pipeline in interactive mode."""
    print_section("INTERACTIVE MODE")
    print("Enter prompts to generate parametric curve drawings")
    print("Type 'quit' or 'exit' to stop")
    print()

    while True:
        try:
            prompt = input("\nEnter a drawing prompt: ").strip()

            if prompt.lower() in ['quit', 'exit', 'q']:
                print("Exiting...")
                break

            if not prompt:
                print("Please enter a non-empty prompt")
                continue

            test_prompt(prompt, "Interactive Test")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main entry point for the test script."""
    if len(sys.argv) > 1:
        # Run with command line argument
        if sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            interactive_mode()
        else:
            # Treat arguments as a prompt
            prompt = " ".join(sys.argv[1:])
            test_prompt(prompt, "Command Line Test")
    else:
        # Run all tests
        run_all_tests()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test script to verify provider connections work with real models."""

import json
import sys
from pathlib import Path

# Add agent to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.providers import provider_from_config, ProviderError


def test_ollama_provider():
    """Test Ollama provider connection."""
    print("\n=== Testing Ollama Provider ===")
    config = {
        "type": "ollama",
        "model": "deepseek-coder:6.7b-instruct",
        "base_url": "http://localhost:11434",
        "use_api": True,
        "timeout": 30
    }

    try:
        provider = provider_from_config(config)
        print(f"✓ Provider created: {provider.name}")
        print(f"✓ Model: {provider.current_model()}")

        # Try listing models
        models = list(provider.list_models())
        if models:
            print(f"✓ Available models: {len(models)}")
            for model in models[:3]:
                print(f"  - {model.name}")
        else:
            print("⚠ No models found (Ollama may not be running)")

        # Try a simple test prompt
        test_prompt = "Write a single line comment explaining what 'Hello World' means."
        print("\n✓ Testing patch generation...")
        result = provider.generate_patch(test_prompt, "/tmp/test_cycle")
        if result:
            print(f"✓ Generated response ({len(result)} chars)")
            print(f"  Preview: {result[:100]}...")
            return True
        else:
            print("✗ No response generated")
            return False

    except ProviderError as e:
        print(f"✗ Provider error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_provider(provider_type, model):
    """Test API provider connection."""
    print(f"\n=== Testing {provider_type.upper()} Provider ===")
    config = {
        "type": provider_type,
        "model": model,
        "temperature": 0.2,
        "timeout": 30
    }

    try:
        provider = provider_from_config(config)
        print(f"✓ Provider created: {provider.name}")
        print(f"✓ Model: {provider.current_model()}")

        # Try a simple test prompt
        test_prompt = "Write a single line comment explaining what 'Hello World' means."
        print("\n✓ Testing patch generation...")
        result = provider.generate_patch(test_prompt, "/tmp/test_cycle")
        if result:
            print(f"✓ Generated response ({len(result)} chars)")
            print(f"  Preview: {result[:100]}...")
            return True
        else:
            print("✗ No response generated")
            return False

    except ProviderError as e:
        print(f"✗ Provider error: {e}")
        print("  (This is expected if API key is not configured)")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def test_config_file():
    """Test loading provider from config file."""
    print("\n=== Testing Config File Provider ===")
    config_path = Path(__file__).parent / "agent" / "config.json"

    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        provider_config = config.get("provider", {})
        print(f"✓ Config loaded")
        print(f"  Type: {provider_config.get('type')}")
        print(f"  Model: {provider_config.get('model')}")

        provider = provider_from_config(provider_config)
        print(f"✓ Provider created: {provider.name}")
        print(f"✓ Current model: {provider.current_model()}")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Provider Connection Test")
    print("=" * 50)

    results = {}

    # Test config file first
    results["config"] = test_config_file()

    # Test Ollama
    results["ollama"] = test_ollama_provider()

    # Test API providers (only if keys are available)
    # Uncomment to test specific providers:
    # results["openai"] = test_api_provider("openai", "gpt-4o-mini")
    # results["anthropic"] = test_api_provider("anthropic", "claude-3-5-sonnet-20241022")
    # results["gemini"] = test_api_provider("gemini", "gemini-2.0-flash")

    print("\n" + "=" * 50)
    print("Test Results:")
    for name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {name:15s} {status}")

    all_passed = all(results.values())
    print("\n" + ("✓ All tests passed!" if all_passed else "⚠ Some tests failed"))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3.11
"""Test script for model configuration and execution."""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_dashboard.core.model_downloader import ModelDownloader


def test_ollama_installed():
    """Test if Ollama is installed."""
    print("\n" + "="*60)
    print("TEST 1: Ollama Installation")
    print("="*60)

    if ModelDownloader.check_ollama_installed():
        print("✓ Ollama is installed")

        # Get version
        try:
            result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
            print(f"  Version: {result.stdout.strip()}")
        except Exception as e:
            print(f"  (Could not get version: {e})")

        return True
    else:
        print("✗ Ollama is NOT installed")
        print("  Install with: brew install ollama")
        return False


def test_ollama_models():
    """Test available Ollama models."""
    print("\n" + "="*60)
    print("TEST 2: Available Ollama Models")
    print("="*60)

    if not ModelDownloader.check_ollama_installed():
        print("✗ Ollama not installed, skipping model check")
        return False

    print("\nChecking recommended models:")
    found_any = False

    for model in ModelDownloader.RECOMMENDED_MODELS:
        exists = ModelDownloader.check_model_exists(model)
        status = "✓ Downloaded" if exists else "✗ Not downloaded"
        print(f"  {status}: {model}")
        if exists:
            found_any = True

    if found_any:
        print("\n✓ At least one model is available")
        return True
    else:
        print("\n✗ No models downloaded yet")
        print("  Download with: ollama pull deepseek-coder:6.7b-instruct")
        return False


def test_model_execution():
    """Test if a model can actually execute."""
    print("\n" + "="*60)
    print("TEST 3: Model Execution")
    print("="*60)

    if not ModelDownloader.check_ollama_installed():
        print("✗ Ollama not installed, skipping execution test")
        return False

    # Find a downloaded model
    test_model = None
    for model in ModelDownloader.RECOMMENDED_MODELS:
        if ModelDownloader.check_model_exists(model):
            test_model = model
            break

    if not test_model:
        print("✗ No models available to test")
        return False

    print(f"\nTesting model: {test_model}")
    print("Sending test prompt...")

    try:
        # Test with a simple prompt
        result = subprocess.run(
            ['ollama', 'run', test_model, 'print("hello")'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print("✓ Model executed successfully")
            print(f"  Output preview: {result.stdout[:100]}...")
            return True
        else:
            print(f"✗ Model execution failed with code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ Model execution timed out (30s)")
        return False
    except Exception as e:
        print(f"✗ Model execution error: {e}")
        return False


def test_api_keys():
    """Test API key storage and retrieval."""
    print("\n" + "="*60)
    print("TEST 4: API Key Storage")
    print("="*60)

    # Check for stored API keys
    has_keys = False

    for provider in ModelDownloader.API_PROVIDERS:
        key = ModelDownloader.get_stored_api_key(provider["type"])
        if key:
            print(f"✓ {provider['label']}: API key stored (***{key[-4:]})")
            has_keys = True
        else:
            print(f"  {provider['label']}: No stored key")

    # Check environment variables
    print("\nChecking environment variables:")
    for provider in ModelDownloader.API_PROVIDERS:
        for env_var in provider["env"]:
            import os
            if os.getenv(env_var):
                print(f"✓ {env_var} is set")
                has_keys = True
            else:
                print(f"  {env_var}: Not set")

    if has_keys:
        print("\n✓ At least one API provider is configured")
        return True
    else:
        print("\n  No API keys configured (Ollama will be used)")
        return False


def test_provider_configuration():
    """Test current provider configuration."""
    print("\n" + "="*60)
    print("TEST 5: Provider Configuration")
    print("="*60)

    provider = ModelDownloader.ensure_provider_configured()

    if provider:
        print(f"✓ Provider configured: {provider.provider_type}")
        print(f"  Model: {provider.model or 'default'}")
        print(f"  Source: {provider.source}")
        return True
    else:
        print("✗ No provider could be configured")
        print("  This should not happen - check installation")
        return False


def test_config_file():
    """Test config file reading/writing."""
    print("\n" + "="*60)
    print("TEST 6: Configuration File")
    print("="*60)

    config_path = ModelDownloader._config_path()
    print(f"Config path: {config_path}")

    if config_path.exists():
        print("✓ Config file exists")

        config = ModelDownloader._load_config()
        if config:
            print("✓ Config file is valid JSON")
            provider = config.get("provider", {})
            if provider:
                print(f"  Provider type: {provider.get('type', 'not set')}")
                print(f"  Model: {provider.get('model', 'not set')}")
            return True
        else:
            print("✗ Config file could not be loaded")
            return False
    else:
        print("  Config file does not exist yet (will be created on first use)")
        return True


def run_all_tests():
    """Run all tests and display summary."""
    print("\n" + "="*70)
    print(" MODEL CONFIGURATION TEST SUITE")
    print("="*70)

    results = {
        "Ollama Installation": test_ollama_installed(),
        "Ollama Models": test_ollama_models(),
        "Model Execution": test_model_execution(),
        "API Keys": test_api_keys(),
        "Provider Configuration": test_provider_configuration(),
        "Config File": test_config_file(),
    }

    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {test_name}")

    passed = sum(results.values())
    total = len(results)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Model configuration is fully functional.")
        return 0
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n⚠️  Some tests failed: {', '.join(failed_tests)}")

        print("\nQuick Fixes:")
        if not results["Ollama Installation"]:
            print("  • Install Ollama: brew install ollama")
        if not results["Ollama Models"]:
            print("  • Download a model: ollama pull deepseek-coder:6.7b-instruct")
        if not results["API Keys"]:
            print("  • Optional: Set API keys in dashboard (press 5 for Model Config)")

        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

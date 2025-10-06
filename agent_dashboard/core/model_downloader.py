"""Auto-download DeepSeek models."""

import subprocess
import os
from pathlib import Path
from typing import Optional


class ModelDownloader:
    """Handles automatic model downloading."""

    # Best DeepSeek models under 60GB
    RECOMMENDED_MODELS = [
        "deepseek-coder:33b",  # ~19GB - Best coding model
        "deepseek-coder:6.7b",  # ~4GB - Fast, good quality
        "deepseek-coder:1.3b",  # ~800MB - Ultra fast
    ]

    @staticmethod
    def check_ollama_installed() -> bool:
        """Check if Ollama is installed."""
        return subprocess.run(['which', 'ollama'], capture_output=True).returncode == 0

    @staticmethod
    def install_ollama():
        """Install Ollama."""
        try:
            # macOS install
            if os.uname().sysname == 'Darwin':
                subprocess.run(['brew', 'install', 'ollama'], check=True)
                return True
            # Linux install
            else:
                subprocess.run(
                    ['curl', '-fsSL', 'https://ollama.com/install.sh'],
                    stdout=subprocess.PIPE
                ).stdout.decode()
                return True
        except Exception:
            return False

    @staticmethod
    def check_model_exists(model_name: str) -> bool:
        """Check if model is already downloaded."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True
            )
            return model_name in result.stdout
        except Exception:
            return False

    @staticmethod
    def download_model(model_name: str) -> bool:
        """Download a model via Ollama."""
        try:
            print(f"\nDownloading {model_name}...")
            print("This may take several minutes depending on model size.")

            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=False,  # Show output to user
                text=True
            )

            return result.returncode == 0
        except Exception as e:
            print(f"Error downloading model: {e}")
            return False

    @staticmethod
    def ensure_model_available() -> Optional[str]:
        """Ensure at least one DeepSeek model is available."""
        # Check if Ollama is installed
        if not ModelDownloader.check_ollama_installed():
            print("Ollama not found. Installing...")
            if not ModelDownloader.install_ollama():
                print("Failed to install Ollama")
                return None

        # Check if any recommended model exists
        for model in ModelDownloader.RECOMMENDED_MODELS:
            if ModelDownloader.check_model_exists(model):
                print(f"Found existing model: {model}")
                return model

        # Download best model
        best_model = ModelDownloader.RECOMMENDED_MODELS[0]
        print(f"\nNo DeepSeek model found. Auto-downloading: {best_model}")
        print("This is a one-time setup (~19GB download)")

        if ModelDownloader.download_model(best_model):
            print(f"✓ Successfully downloaded {best_model}")
            return best_model
        else:
            # Try smaller model
            fallback = ModelDownloader.RECOMMENDED_MODELS[1]
            print(f"Trying smaller model: {fallback}")
            if ModelDownloader.download_model(fallback):
                print(f"✓ Successfully downloaded {fallback}")
                return fallback

        print("Failed to download any model")
        return None

    @staticmethod
    def configure_agent_for_ollama(model_name: str):
        """Configure agent config.json to use Ollama model."""
        config_path = Path.cwd() / "agent" / "config.json"

        if not config_path.exists():
            # Create default config
            config = {
                "provider": {
                    "type": "ollama",
                    "model": model_name,
                    "base_url": "http://localhost:11434"
                },
                "loop": {
                    "max_cycles": 0,  # Never stop
                    "cooldown_seconds": 10,
                    "apply_patches": True,
                    "require_manual_approval": False
                }
            }
        else:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Update provider
            config.setdefault('provider', {})
            config['provider']['type'] = 'ollama'
            config['provider']['model'] = model_name
            config['provider']['base_url'] = 'http://localhost:11434'

        # Write config
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Configured agent to use {model_name}")

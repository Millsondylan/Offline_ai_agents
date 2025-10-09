"""Auto-download DeepSeek models."""

import subprocess
import os
from pathlib import Path
from typing import Optional


class ModelDownloader:
    """Handles automatic model downloading."""

    # Best DeepSeek models under 60GB - prefer instruct variants
    RECOMMENDED_MODELS = [
        "deepseek-coder:6.7b-instruct",  # ~4GB - Fast, good quality (instruct variant) - PREFERRED
        "deepseek-coder:33b",  # ~19GB - Best coding model
        "deepseek-coder:6.7b",  # ~4GB - Fast, good quality (base variant)
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
            # Check for exact match in the model name column
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                if line.strip():
                    actual_model = line.split()[0]  # First column is model name
                    if actual_model == model_name:
                        return True
            return False
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

        # Check if any recommended model exists, prefer instruct variants
        found_models = []
        for model in ModelDownloader.RECOMMENDED_MODELS:
            if ModelDownloader.check_model_exists(model):
                found_models.append(model)
                print(f"Found existing model: {model}")

        # If we found models, prefer instruct variant
        if found_models:
            # Prefer instruct variants
            for model in found_models:
                if "instruct" in model:
                    return model
            # If no instruct variant, return first found
            return found_models[0]

        # Download best model (now the instruct variant)
        best_model = ModelDownloader.RECOMMENDED_MODELS[0]
        print(f"\nNo DeepSeek model found. Auto-downloading: {best_model}")
        print("This is a one-time setup (~4GB download)")

        if ModelDownloader.download_model(best_model):
            print(f"✓ Successfully downloaded {best_model}")
            return best_model
        else:
            # Try next model
            fallback = ModelDownloader.RECOMMENDED_MODELS[1]
            print(f"Trying alternative model: {fallback}")
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
            # Create comprehensive default config
            config = {
                "provider": {
                    "type": "ollama",
                    "model": model_name,
                    "command": {
                        "args": ["bash", "-lc", "bash agent/local/ollama_provider.sh"],
                        "timeout": 1200
                    },
                    "base_url": "http://localhost:11434"
                },
                "available_models": ["llama3", "gpt-4", "claude-sonnet-4", "gemini-2.0-flash"],
                "loop": {
                    "max_cycles": 3,  # Reasonable limit
                    "cooldown_seconds": 10,
                    "apply_patches": True,
                    "require_manual_approval": False,
                    "fast_path_on_fs_change": True
                },
                "sessions": {
                    "enabled": True,
                    "default_duration_seconds": 3600,
                    "default_post_review_delay_seconds": 3600,
                    "max_duration_seconds": 28800
                },
                "commands": {
                    "analyze": {"enabled": True, "cmd": "ruff check", "timeout": 900},
                    "test": {"enabled": True, "cmd": "pytest -q", "timeout": 3600},
                    "e2e": {"enabled": False, "cmd": "", "timeout": 7200},
                    "screenshots": {"enabled": False, "cmd": "", "timeout": 600}
                },
                "gate": {
                    "min_coverage": 0.8,
                    "ruff_fix": True,
                    "bandit_fail_levels": ["HIGH", "CRITICAL"],
                    "semgrep_rules": ["p/ci", "p/python"],
                    "pip_audit_fix": False,
                    "allow_override": False
                },
                "git": {
                    "commit": True,
                    "branch": "agent/main",
                    "push": False,
                    "remote": "origin",
                    "push_interval_seconds": 900,
                    "commit_cadence_seconds": 3600,
                    "auto_commit": True
                },
                "tui": {
                    "refresh_hz": 15,
                    "show_thinking": True,
                    "theme": "auto"
                }
            }
        else:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Only update the model if it's different - preserve other settings
            config.setdefault('provider', {})
            current_model = config['provider'].get('model', '')

            if current_model != model_name:
                config['provider']['type'] = 'ollama'
                config['provider']['model'] = model_name
                config['provider']['base_url'] = 'http://localhost:11434'

                # Ensure command args exist for ollama
                config['provider'].setdefault('command', {})
                config['provider']['command']['args'] = ["bash", "-lc", "bash agent/local/ollama_provider.sh"]
                config['provider']['command']['timeout'] = 1200

                # Only update max_cycles if it's 0 (infinite) - preserve user settings otherwise
                if config.get('loop', {}).get('max_cycles', 0) == 0:
                    config.setdefault('loop', {})
                    config['loop']['max_cycles'] = 3

                print(f"✓ Updated agent model from {current_model} to {model_name}")
            else:
                print(f"✓ Agent already configured for {model_name}")
                return  # Don't rewrite config if no changes needed

        # Write config
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✓ Configured agent to use {model_name}")

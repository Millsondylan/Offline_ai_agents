"""Provider detection and optional model downloads."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class ProviderInfo:
    """Description of the configured provider."""

    provider_type: str
    model: Optional[str]
    source: str  # e.g. "config", "env", "download"


class ModelDownloader:
    """Handles automatic model downloading."""

    # Best DeepSeek models under 60GB - prefer instruct variants
    RECOMMENDED_MODELS = [
        "deepseek-coder:6.7b-instruct",  # ~4GB - Fast, good quality (instruct variant) - PREFERRED
        "deepseek-coder:33b",  # ~19GB - Best coding model
        "deepseek-coder:6.7b",  # ~4GB - Fast, good quality (base variant)
        "deepseek-coder:1.3b",  # ~800MB - Ultra fast
    ]

    API_PROVIDERS = [
        {"type": "openai", "env": ["OPENAI_API_KEY"], "model": "gpt-4o-mini", "label": "OpenAI"},
        {"type": "anthropic", "env": ["ANTHROPIC_API_KEY"], "model": "claude-3-5-sonnet", "label": "Anthropic Claude"},
        {"type": "gemini", "env": ["GOOGLE_API_KEY", "GEMINI_API_KEY"], "model": "gemini-2.0-flash", "label": "Google Gemini"},
    ]

    @staticmethod
    def _config_path() -> Path:
        return Path.cwd() / "agent" / "config.json"

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_config() -> Optional[Dict[str, Any]]:
        path = ModelDownloader._config_path()
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _save_config(config: Dict[str, Any]) -> None:
        path = ModelDownloader._config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2))

    @staticmethod
    def _base_config() -> Dict[str, Any]:
        return {
            "provider": {},
            "available_models": ["llama3", "gpt-4", "claude-3-5-sonnet", "gemini-2.0-flash"],
            "loop": {
                "max_cycles": 3,
                "cooldown_seconds": 10,
                "apply_patches": True,
                "require_manual_approval": False,
                "fast_path_on_fs_change": True,
            },
            "sessions": {
                "enabled": True,
                "default_duration_seconds": 3600,
                "default_post_review_delay_seconds": 3600,
                "max_duration_seconds": 28800,
            },
            "commands": {
                "analyze": {"enabled": True, "cmd": "ruff check", "timeout": 900},
                "test": {"enabled": True, "cmd": "pytest -q", "timeout": 3600},
                "e2e": {"enabled": False, "cmd": "", "timeout": 7200},
                "screenshots": {"enabled": False, "cmd": "", "timeout": 600},
            },
            "gate": {
                "min_coverage": 0.8,
                "ruff_fix": True,
                "bandit_fail_levels": ["HIGH", "CRITICAL"],
                "semgrep_rules": ["p/ci", "p/python"],
                "pip_audit_fix": False,
                "allow_override": False,
            },
            "git": {
                "commit": True,
                "branch": "agent/main",
                "push": False,
                "remote": "origin",
                "push_interval_seconds": 900,
                "commit_cadence_seconds": 3600,
                "auto_commit": True,
            },
            "tui": {
                "refresh_hz": 15,
                "show_thinking": True,
                "theme": "auto",
            },
        }

    @staticmethod
    def _ensure_config() -> Dict[str, Any]:
        """Return a config dict, creating defaults if needed."""
        config = ModelDownloader._load_config()
        if config is None:
            config = ModelDownloader._base_config()
        else:
            config.setdefault("provider", {})
        return config

    @staticmethod
    def _key_store_path() -> Path:
        return Path.cwd() / "agent" / "local" / "api_keys.json"

    @staticmethod
    def _read_api_keys() -> Dict[str, str]:
        path = ModelDownloader._key_store_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _write_api_keys(data: Dict[str, str]) -> None:
        path = ModelDownloader._key_store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    @staticmethod
    def store_api_key(provider_type: str, api_key: str) -> None:
        """Persist an API key for later reuse."""
        keys = ModelDownloader._read_api_keys()
        keys[provider_type] = api_key
        ModelDownloader._write_api_keys(keys)

    @staticmethod
    def get_stored_api_key(provider_type: str) -> Optional[str]:
        return ModelDownloader._read_api_keys().get(provider_type)

    # ------------------------------------------------------------------
    # Provider validation
    # ------------------------------------------------------------------
    @staticmethod
    def _get_env_key(keys: List[str]) -> Tuple[Optional[str], Optional[str]]:
        for key in keys:
            value = os.getenv(key)
            if value:
                return key, value
        return None, None

    @staticmethod
    def _resolve_api_key(entry: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], str]:
        """Return (env_var, value, source) for the given provider entry."""
        env_var, value = ModelDownloader._get_env_key(entry["env"])
        if value:
            return env_var, value, "env"

        stored = ModelDownloader.get_stored_api_key(entry["type"])
        if stored:
            env_var = entry["env"][0]
            os.environ.setdefault(env_var, stored)
            return env_var, stored, "stored"

        return None, None, ""

    @staticmethod
    def _validate_ollama_provider(config: Dict[str, Any]) -> Tuple[bool, str]:
        provider = config.get("provider", {})
        model = provider.get("model")
        if not ModelDownloader.check_ollama_installed():
            return False, "Ollama is not installed"
        if not model:
            return False, "No model specified for Ollama provider"
        if not ModelDownloader.check_model_exists(model):
            return False, f"Model '{model}' not present locally"
        return True, ""

    @staticmethod
    def _validate_api_provider(provider_type: str) -> Tuple[bool, str]:
        entry = next((p for p in ModelDownloader.API_PROVIDERS if p["type"] == provider_type), None)
        if not entry:
            return False, f"Unknown provider type '{provider_type}'"
        _, value, _ = ModelDownloader._resolve_api_key(entry)
        if not value:
            env_list = ", ".join(entry["env"])
            return False, f"Missing API key for {provider_type} ({env_list})"
        return True, ""

    @staticmethod
    def _validate_existing_config(config: Dict[str, Any]) -> Tuple[bool, Optional[ProviderInfo], str]:
        provider = config.get("provider") or {}
        provider_type = provider.get("type")
        model = provider.get("model")

        if not provider_type:
            return False, None, "No provider configured"

        if provider_type == "ollama":
            ok, reason = ModelDownloader._validate_ollama_provider(config)
            if ok:
                return True, ProviderInfo("ollama", model, "config"), ""
            return False, None, reason

        ok, reason = ModelDownloader._validate_api_provider(provider_type)
        if ok:
            entry = next((p for p in ModelDownloader.API_PROVIDERS if p["type"] == provider_type), None)
            _, _, source = ModelDownloader._resolve_api_key(entry) if entry else (None, None, "config")
            return True, ProviderInfo(provider_type, model, source or "config"), ""
        return False, None, reason

    # ------------------------------------------------------------------
    # Provider configuration
    # ------------------------------------------------------------------
    @staticmethod
    def _configure_api_provider(provider_type: str, model: str, source: str = "env") -> ProviderInfo:
        config = ModelDownloader._ensure_config()
        provider = config.setdefault("provider", {})

        provider["type"] = provider_type
        provider["model"] = model
        provider.pop("command", None)
        provider.pop("base_url", None)

        ModelDownloader._save_config(config)
        print(f"✓ Configured agent to use {provider_type} ({model}) via API keys")
        return ProviderInfo(provider_type, model, source)

    @staticmethod
    def configure_agent_for_ollama(model_name: str) -> ProviderInfo:
        """Configure agent config.json to use Ollama model."""
        config = ModelDownloader._ensure_config()
        provider = config.setdefault("provider", {})

        provider.update(
            {
                "type": "ollama",
                "model": model_name,
                "base_url": "http://localhost:11434",
                "command": {
                    "args": ["bash", "-lc", "bash agent/local/ollama_provider.sh"],
                    "timeout": 1200,
                },
            }
        )

        ModelDownloader._save_config(config)
        print(f"✓ Configured agent to use local model {model_name}")
        return ProviderInfo("ollama", model_name, "download")

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
    def _ensure_local_model() -> Optional[str]:
        """Ensure at least one DeepSeek model is available locally."""
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
    def ensure_provider_configured() -> Optional[ProviderInfo]:
        """Ensure the agent has a usable provider, preferring existing config > API keys > local model."""

        config = ModelDownloader._load_config()
        if config:
            valid, info, reason = ModelDownloader._validate_existing_config(config)
            if valid and info:
                print(f"✓ Using existing provider from config: {info.provider_type} ({info.model or 'default'})")
                return info
            elif reason:
                print(f"Config provider invalid: {reason}")

        # Check API keys in priority order
        for entry in ModelDownloader.API_PROVIDERS:
            env_var, value, source = ModelDownloader._resolve_api_key(entry)
            if value:
                info = ModelDownloader._configure_api_provider(entry["type"], entry["model"], source or "env")
                origin = "stored key" if source == "stored" else f"{env_var}"
                print(f"✓ Detected {entry['type']} via {origin}")
                return info

        # Fallback to local model using Ollama
        model = ModelDownloader._ensure_local_model()
        if model:
            info = ModelDownloader.configure_agent_for_ollama(model)
            return info

        print("No provider could be configured automatically.")
        print("Options:")
        print("  • Install Ollama and download a DeepSeek model")
        print("  • Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY / GEMINI_API_KEY")
        return None

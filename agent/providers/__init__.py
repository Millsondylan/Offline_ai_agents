from __future__ import annotations

from typing import Dict, Optional

from .api import HostedAPIProvider
from .base import ModelInfo, Provider, ProviderError
from .command import CommandProvider
from .keys import KeyStore
from .manual import ManualProvider
from .ollama import OllamaProvider

__all__ = [
    "Provider",
    "ProviderError",
    "ManualProvider",
    "CommandProvider",
    "OllamaProvider",
    "HostedAPIProvider",
    "KeyStore",
    "provider_from_config",
    "ModelInfo",
]


def provider_from_config(cfg: Dict, keystore: Optional[KeyStore] = None) -> Provider:
    """Instantiate a provider from config block."""

    keystore = keystore or KeyStore()
    ptype = (cfg or {}).get("type", "manual").lower()
    if ptype == "manual":
        return ManualProvider(cfg.get("manual", {}))
    if ptype == "command":
        command_cfg = dict(cfg.get("command", {}))
        return CommandProvider(command_cfg)
    if ptype in {"ollama", "local"}:
        ollama_cfg = dict(cfg.get("command", {}))
        # Allow shorthand `provider.model`
        if "model" not in ollama_cfg and cfg.get("model"):
            ollama_cfg["model"] = cfg["model"]
        return OllamaProvider(ollama_cfg)
    if ptype == "api":
        api_cfg = dict(cfg.get("api", {}))
        if cfg.get("model") and "model" not in api_cfg:
            api_cfg["model"] = cfg["model"]
        if cfg.get("backend") and "backend" not in api_cfg:
            api_cfg["backend"] = cfg["backend"]
        return HostedAPIProvider(api_cfg, keystore=keystore)
    raise ProviderError(f"unknown provider type: {ptype}")

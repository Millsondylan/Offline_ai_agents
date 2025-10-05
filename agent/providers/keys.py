from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency
    import keyring  # type: ignore
except Exception:  # pragma: no cover - keyring not available
    keyring = None  # type: ignore


class KeyStore:
    """Store provider secrets using keyring when available.

    Falls back to environment variables (read-only) and finally a local
    plaintext file restricted to the current user. The fallback is not
    encrypted but keeps everything within ``agent/local/keys`` which is
    gitignored by default.
    """

    def __init__(
        self,
        service: str = "offline-agent",
        env_prefix: str = "AGENT_API_KEY_",
        local_dir: Optional[Path] = None,
    ) -> None:
        self.service = service
        self.env_prefix = env_prefix
        repo_root = Path(__file__).resolve().parents[2]
        default_dir = repo_root / "agent" / "local" / "keys"
        self.local_dir = local_dir or default_dir
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def _env_var(self, provider: str) -> str:
        return f"{self.env_prefix}{provider.upper()}"

    def get(self, provider: str) -> Optional[str]:
        env_key = self._env_var(provider)
        if env_key in os.environ:
            return os.environ[env_key]
        if keyring is not None:
            try:
                secret = keyring.get_password(self.service, provider)
                if secret:
                    return secret
            except Exception:
                pass
        path = self.local_dir / f"{provider}.key"
        if path.exists():
            return path.read_text(encoding="utf-8").strip() or None
        return None

    def set(self, provider: str, secret: str) -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        if keyring is not None:
            try:
                keyring.set_password(self.service, provider, secret)
                return
            except Exception:
                # Fall back to file storage.
                pass
        path = self.local_dir / f"{provider}.key"
        path.write_text(secret, encoding="utf-8")
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

    def clear(self, provider: str) -> None:
        if keyring is not None:
            try:
                keyring.delete_password(self.service, provider)
            except keyring.errors.PasswordDeleteError:  # type: ignore[attr-defined]
                pass
            except Exception:
                pass
        env_key = self._env_var(provider)
        if env_key in os.environ:
            # Environment variables are read-only; warn via return value.
            pass
        path = self.local_dir / f"{provider}.key"
        if path.exists():
            path.unlink()

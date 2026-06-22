"""
SecureTokenStore — безопасное хранение OAuth-токенов.

Backend priority (auto-detect):
1. keyring (OS-native: macOS Keychain, Linux Secret Service, Windows Credential Manager)
2. Encrypted file (Fernet, key from SELFOS_TOKEN_KEY env or generated)
3. Plain JSON (fallback with warning)

Profile-aware: tokens stored under ~/.selfos/profiles/{profile}/tokens/
"""

from __future__ import annotations

import json
import logging
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    """OAuth 2.0 token data."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"
    expires_at: float | None = None  # Unix timestamp
    scopes: list[str] | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, leeway: float = 60.0) -> bool:
        """Проверить, истёк ли токен (с запасом в leeway секунд)."""
        if self.expires_at is None:
            return False
        import time
        return time.time() + leeway >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "access_token": self.access_token,
            "token_type": self.token_type,
        }
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
        if self.expires_at is not None:
            result["expires_at"] = self.expires_at
        if self.scopes:
            result["scopes"] = self.scopes
        if self.raw:
            result["raw"] = self.raw
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OAuthToken:
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=data.get("expires_at"),
            scopes=data.get("scopes"),
            raw=data.get("raw", {}),
        )


class SecureTokenStore:
    """
    Хранение OAuth-токенов.
    
    Backend auto-detection:
    1. keyring — если установлен
    2. Encrypted file (Fernet) — если cryptography установлен
    3. Plain JSON — fallback (выводит warning)
    """

    _KEYRING_SERVICE = "selfos"

    def __init__(self, profile: str = "default") -> None:
        self._profile = profile
        self._backend: str = "plain"  # default fallback
        self._keyring = None
        self._fernet = None

        # Try keyring first
        try:
            import keyring as _kr  # type: ignore[import-untyped]
            self._keyring = _kr
            self._backend = "keyring"
            logger.debug("TokenStore backend: keyring")
            return
        except ImportError:
            pass

        # Try encrypted file
        try:
            from cryptography.fernet import Fernet as _Fernet  # noqa: F811
            key = self._load_or_generate_fernet_key()
            self._fernet = _Fernet(key)
            self._backend = "encrypted_file"
            logger.debug("TokenStore backend: encrypted_file")
            return
        except ImportError:
            pass

        # Plain JSON fallback
        warnings.warn(
            "SecureTokenStore: no keyring or cryptography available. "
            "Tokens will be stored as plain JSON. "
            "Install: pip install selfos[security]",
            UserWarning,
            stacklevel=2,
        )
        logger.warning("TokenStore backend: plain JSON (INSECURE)")

    # ─── Public API ────────────────────────────────────────────────────

    def save(self, provider: str, token: OAuthToken) -> None:
        """Сохранить токен для указанного провайдера."""
        if self._backend == "keyring":
            self._save_keyring(provider, token)
        elif self._backend == "encrypted_file":
            self._save_encrypted(provider, token)
        else:
            self._save_plain(provider, token)

    def load(self, provider: str) -> OAuthToken | None:
        """Загрузить токен для провайдера. None если нет."""
        if self._backend == "keyring":
            return self._load_keyring(provider)
        elif self._backend == "encrypted_file":
            return self._load_encrypted(provider)
        else:
            return self._load_plain(provider)

    def delete(self, provider: str) -> bool:
        """Удалить токен провайдера. True если был удалён."""
        if self._backend == "keyring":
            return self._delete_keyring(provider)
        elif self._backend == "encrypted_file":
            return self._delete_file(provider)
        else:
            return self._delete_file(provider)

    def list_providers(self) -> list[str]:
        """Список провайдеров, для которых есть токены."""
        tokens_dir = self._tokens_dir()
        if not tokens_dir.exists():
            return []
        providers: list[str] = []
        for f in tokens_dir.iterdir():
            if f.suffix in (".json", ".enc"):
                providers.append(f.stem)
        return sorted(providers)

    def profile(self) -> str:
        return self._profile

    # ─── Backend: keyring ───────────────────────────────────────────────

    def _save_keyring(self, provider: str, token: OAuthToken) -> None:
        assert self._keyring is not None
        data = json.dumps(token.to_dict())
        self._keyring.set_password(self._KEYRING_SERVICE, provider, data)

    def _load_keyring(self, provider: str) -> OAuthToken | None:
        assert self._keyring is not None
        data = self._keyring.get_password(self._KEYRING_SERVICE, provider)
        if data is None:
            return None
        try:
            parsed = json.loads(data)
            return OAuthToken.from_dict(parsed)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to decode token for %s: %s", provider, e)
            return None

    def _delete_keyring(self, provider: str) -> bool:
        assert self._keyring is not None
        existing = self._keyring.get_password(self._KEYRING_SERVICE, provider)
        if existing is None:
            return False
        self._keyring.delete_password(self._KEYRING_SERVICE, provider)
        return True

    # ─── Backend: encrypted file ────────────────────────────────────────

    def _load_or_generate_fernet_key(self) -> bytes:
        """Загрузить ключ из env или сгенерировать и сохранить."""
        from cryptography.fernet import Fernet  # noqa: F811

        env_key = os.environ.get("SELFOS_TOKEN_KEY")
        if env_key:
            return env_key.encode()

        key_file = self._tokens_dir().parent / ".token_key"
        if key_file.exists():
            return key_file.read_bytes()

        # Generate new key
        key = Fernet.generate_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_bytes(key)
        os.chmod(str(key_file), 0o600)  # Owner read/write only
        return key

    def _save_encrypted(self, provider: str, token: OAuthToken) -> None:
        assert self._fernet is not None
        data = json.dumps(token.to_dict())
        encrypted = self._fernet.encrypt(data.encode("utf-8"))
        path = self._token_path(provider, suffix=".enc")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encrypted)
        os.chmod(str(path), 0o600)

    def _load_encrypted(self, provider: str) -> OAuthToken | None:
        from cryptography.fernet import InvalidToken

        assert self._fernet is not None
        path = self._token_path(provider, suffix=".enc")
        if not path.exists():
            return None
        try:
            encrypted = path.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            parsed = json.loads(decrypted.decode("utf-8"))
            return OAuthToken.from_dict(parsed)
        except (InvalidToken, json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to decrypt token for %s: %s", provider, e)
            return None

    # ─── Backend: plain JSON ────────────────────────────────────────────

    def _save_plain(self, provider: str, token: OAuthToken) -> None:
        path = self._token_path(provider, suffix=".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(token.to_dict(), indent=2))
        os.chmod(str(path), 0o600)

    def _load_plain(self, provider: str) -> OAuthToken | None:
        path = self._token_path(provider, suffix=".json")
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return OAuthToken.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to read token for %s: %s", provider, e)
            return None

    # ─── Shared helpers ─────────────────────────────────────────────────

    def _delete_file(self, provider: str) -> bool:
        deleted = False
        for suffix in (".json", ".enc"):
            path = self._token_path(provider, suffix=suffix)
            if path.exists():
                path.unlink()
                deleted = True
        return deleted

    def _tokens_dir(self) -> Path:
        from selfos.config import profile_dir as _pd
        return _pd(self._profile) / "tokens"

    def _token_path(self, provider: str, suffix: str = ".json") -> Path:
        return self._tokens_dir() / f"{provider}{suffix}"

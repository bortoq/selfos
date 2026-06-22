"""
OAuthManager — единый менеджер OAuth2 аутентификации.

Поддерживает:
- Browser-based flow (http://localhost:{port}/callback)
- Device flow (для headless/SSH/CI)
- Token refresh
- Provider-agnostic дизайн (Google, GitHub, Todoist, etc.)
"""

from __future__ import annotations

import logging
import socketserver
import time
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler
from typing import Any, cast
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from selfos.integrations.token_store import OAuthToken, SecureTokenStore

logger = logging.getLogger(__name__)


@dataclass
class OAuthProviderConfig:
    """Конфигурация OAuth2 провайдера."""

    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: list[str]
    device_auth_url: str | None = None
    revoke_url: str | None = None
    redirect_uri: str = "http://localhost:8080/callback"
    extra_auth_params: dict[str, str] = field(default_factory=dict)
    extra_token_params: dict[str, str] = field(default_factory=dict)


# ─── Predefined provider configurations ────────────────────────────────

GOOGLE_GMAIL_CONFIG = OAuthProviderConfig(
    client_id="",  # User provides their own
    client_secret="",
    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    device_auth_url="https://oauth2.googleapis.com/device/code",
    revoke_url="https://oauth2.googleapis.com/revoke",
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.labels",
    ],
    redirect_uri="http://localhost:8080/callback",
    extra_auth_params={"access_type": "offline", "prompt": "consent"},
)

GOOGLE_CALENDAR_CONFIG = OAuthProviderConfig(
    client_id="",
    client_secret="",
    auth_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    device_auth_url="https://oauth2.googleapis.com/device/code",
    scopes=["https://www.googleapis.com/auth/calendar.events"],
    redirect_uri="http://localhost:8080/callback",
    extra_auth_params={"access_type": "offline", "prompt": "consent"},
)

GITHUB_CONFIG = OAuthProviderConfig(
    client_id="",
    client_secret="",
    auth_url="https://github.com/login/oauth/authorize",
    token_url="https://github.com/login/oauth/access_token",
    scopes=["repo", "notifications"],
    redirect_uri="http://localhost:8080/callback",
)


def _get_provider_configs() -> dict[str, OAuthProviderConfig]:
    """Возвращает словарь предопределённых конфигураций провайдеров."""
    return {
        "gmail": GOOGLE_GMAIL_CONFIG,
        "calendar": GOOGLE_CALENDAR_CONFIG,
        "github": GITHUB_CONFIG,
    }


# ─── OAuth Manager ─────────────────────────────────────────────────────


class OAuthError(Exception):
    """Ошибка OAuth2 аутентификации."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class OAuthManager:
    """
    Единый менеджер OAuth2 аутентификации.
    
    Использование:
        config = OAuthProviderConfig(...)
        store = SecureTokenStore(profile="default")
        manager = OAuthManager("gmail", config, store)
        
        # Browser flow
        token = manager.start_browser_flow()
        
        # Device flow
        token = manager.start_device_flow()
        
        # Get valid token (auto-refresh)
        token = manager.get_valid_token()
    """

    def __init__(
        self,
        provider_name: str,
        config: OAuthProviderConfig,
        token_store: SecureTokenStore,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._provider = provider_name
        self._config = config
        self._store = token_store
        self._http = http_client or httpx.Client(timeout=30.0)

    # ─── Public API ────────────────────────────────────────────────────

    def start_browser_flow(self, port: int = 8080) -> OAuthToken:
        """
        Browser-based OAuth2 flow.
        
        Запускает локальный HTTP-сервер на localhost:{port},
        открывает браузер для авторизации, обрабатывает callback.
        """
        redirect_uri = f"http://localhost:{port}/callback"

        # Start local server to receive callback
        token = self._receive_callback(port, redirect_uri)

        # Exchange auth code for tokens
        if not token:
            raise OAuthError("No authorization code received")

        return token

    def start_device_flow(self) -> OAuthToken:
        """
        Device flow для headless сред (SSH, CI, сервер).
        
        Показывает код на экране, пользователь вводит его на устройстве.
        """
        if not self._config.device_auth_url:
            raise OAuthError(
                f"Provider '{self._provider}' does not support device flow"
            )

        # Request device code
        device_data = self._request_device_code()

        # Display instructions
        verification_url = device_data.get("verification_url",
                                           device_data.get("verification_uri",
                                                           "https://google.com/device"))
        user_code = device_data["user_code"]
        device_code = device_data["device_code"]
        interval = device_data.get("interval", 5)

        print("\n=== OAuth Device Flow ===")
        print(f"Provider: {self._provider}")
        print(f"1. Go to: {verification_url}")
        print(f"2. Enter code: {user_code}")
        print("\nWaiting for authorization...")

        # Poll for token
        token_data = self._poll_device_code(device_code, interval)
        return self._parse_token_response(token_data)

    def get_valid_token(self) -> OAuthToken:
        """
        Получить валидный токен (из хранилища или с refresh-ом).
        
        Raises:
            OAuthError: если токен отсутствует и не может быть получен.
        """
        token = self._store.load(self._provider)
        if token is None:
            raise OAuthError(
                f"No token found for '{self._provider}'. "
                f"Run 'selfos plugin setup {self._provider}' first."
            )

        if not token.is_expired():
            return token

        if token.refresh_token is None:
            raise OAuthError(
                f"Token for '{self._provider}' has expired and no refresh token available. "
                f"Run 'selfos plugin setup {self._provider}' to re-authenticate."
            )

        # Refresh token
        return self._refresh_access_token(token.refresh_token)

    def revoke_token(self) -> bool:
        """Отозвать токен (если провайдер поддерживает)."""
        if not self._config.revoke_url:
            return False

        token = self._store.load(self._provider)
        if token is None:
            return False

        try:
            resp = self._http.post(
                self._config.revoke_url,
                data={"token": token.access_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            self._store.delete(self._provider)
            return resp.status_code < 400
        except httpx.HTTPError as e:
            logger.warning("Token revocation failed: %s", e)
            return False

    def test_connection(self) -> bool:
        """Проверить, что сохранённый токен работает."""
        try:
            token = self.get_valid_token()
            # Make a lightweight API call to verify
            return self._verify_token(token)
        except (OAuthError, httpx.HTTPError) as e:
            logger.warning("Connection test failed: %s", e)
            return False

    # ─── Browser flow internals ─────────────────────────────────────────

    def _build_auth_url(self, redirect_uri: str) -> str:
        """Собрать URL для редиректа пользователя на страницу авторизации."""
        params = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._config.scopes),
        }
        params.update(self._config.extra_auth_params)
        return f"{self._config.auth_url}?{urlencode(params)}"

    def _receive_callback(self, port: int, redirect_uri: str) -> OAuthToken:
        """
        Запустить временный HTTP-сервер для получения callback.
        
        Обрабатывает GET /callback?code=... и обменивает код на токен.
        """
        auth_code: list[str] = []
        error_msg: list[str] = []

        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:
                pass  # Silence HTTP server logs

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)

                if "code" in params:
                    auth_code.append(params["code"][0])
                    self._respond(
                        200,
                        "<html><body><h1>✅ Authorization successful!</h1>"
                        "<p>You can close this window.</p></body></html>"
                    )
                elif "error" in params:
                    error_msg.append(params.get("error", ["unknown"])[0])
                    self._respond(
                        400,
                        f"<html><body><h1>❌ Authorization failed</h1>"
                        f"<p>Error: {params['error'][0]}</p></body></html>"
                    )
                else:
                    self._respond(
                        400,
                        "<html><body><h1>❌ Missing authorization code</h1></body></html>"
                    )

            def _respond(self, status: int, body: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))

        # Open browser and start server
        auth_url = self._build_auth_url(redirect_uri)
        webbrowser.open(auth_url)

        # Single-use server
        with socketserver.TCPServer(("", port), CallbackHandler) as httpd:
            httpd.timeout = 300  # 5 minutes
            while not auth_code and not error_msg:
                httpd.handle_request()

        if error_msg:
            raise OAuthError(f"Authorization denied: {error_msg[0]}")

        # Exchange code for token
        return self._exchange_code(auth_code[0], redirect_uri)

    def _exchange_code(self, code: str, redirect_uri: str) -> OAuthToken:
        """Обменять authorization code на token."""
        data = {
            "code": code,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        data.update(self._config.extra_token_params)

        try:
            resp = self._http.post(
                self._config.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
            if resp.status_code >= 400:
                raise OAuthError(
                    f"Token exchange failed: {resp.text}",
                    status_code=resp.status_code,
                )
            token_data = resp.json()
            token = self._parse_token_response(token_data)
            self._store.save(self._provider, token)
            return token
        except httpx.HTTPError as e:
            raise OAuthError(f"Token exchange HTTP error: {e}") from e

    # ─── Device flow internals ──────────────────────────────────────────

    def _request_device_code(self) -> dict[str, Any]:
        """Запросить device code у провайдера."""
        assert self._config.device_auth_url is not None
        try:
            resp = self._http.post(
                self._config.device_auth_url,
                data={
                    "client_id": self._config.client_id,
                    "scope": " ".join(self._config.scopes),
                },
                headers={"Accept": "application/json"},
            )
            if resp.status_code >= 400:
                raise OAuthError(
                    f"Device code request failed: {resp.text}",
                    status_code=resp.status_code,
                )
            return cast(dict[str, Any], resp.json())
        except httpx.HTTPError as e:
            raise OAuthError(f"Device code HTTP error: {e}") from e

    def _poll_device_code(self, device_code: str, interval: int) -> dict[str, Any]:
        """Poll провайдера до получения токена или истечения времени."""
        import time as _time

        expiration = 600  # 10 minutes max
        deadline = _time.time() + expiration

        while _time.time() < deadline:
            _time.sleep(interval)

            try:
                resp = self._http.post(
                    self._config.token_url,
                    data={
                        "client_id": self._config.client_id,
                        "client_secret": self._config.client_secret,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                )

                result = cast(dict[str, Any], resp.json())
                error = result.get("error")

                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                elif error == "access_denied":
                    raise OAuthError("Device flow denied by user")
                elif error == "expired_token":
                    raise OAuthError("Device code expired, please retry")
                elif error:
                    raise OAuthError(f"Device flow error: {error}")

                return result

            except httpx.HTTPError as e:
                if _time.time() < deadline:
                    _time.sleep(interval)
                    continue
                raise OAuthError(f"Device flow HTTP error: {e}") from e

        raise OAuthError("Device flow timed out (10 minutes)")

    # ─── Token refresh ──────────────────────────────────────────────────

    def _refresh_access_token(self, refresh_token: str) -> OAuthToken:
        """Обновить access token через refresh token."""
        data = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        data.update(self._config.extra_token_params)

        try:
            resp = self._http.post(
                self._config.token_url,
                data=data,
                headers={"Accept": "application/json"},
            )
            if resp.status_code >= 400:
                raise OAuthError(
                    f"Token refresh failed: {resp.text}",
                    status_code=resp.status_code,
                )
            token_data = cast(dict[str, Any], resp.json())
            # Keep the old refresh token if the provider doesn't return a new one
            if "refresh_token" not in token_data:
                old_token = self._store.load(self._provider)
                if old_token and old_token.refresh_token:
                    token_data["refresh_token"] = old_token.refresh_token
            token = self._parse_token_response(token_data)
            self._store.save(self._provider, token)
            return token
        except httpx.HTTPError as e:
            raise OAuthError(f"Token refresh HTTP error: {e}") from e

    # ─── Helpers ─────────────────────────────────────────────────────────

    def _parse_token_response(self, data: dict[str, Any]) -> OAuthToken:
        """Распарсить ответ токен-эндпоинта в OAuthToken."""
        expires_in = data.get("expires_in")
        expires_at = (time.time() + expires_in) if expires_in else None

        return OAuthToken(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            token_type=data.get("token_type", "Bearer"),
            expires_at=expires_at,
            scopes=data.get("scope", "").split() if data.get("scope") else None,
            raw=data,
        )

    def _verify_token(self, token: OAuthToken) -> bool:
        """
        Проверить, что токен рабочий.
        
        Для Google: вызов Gmail API profile.
        Для других провайдеров: зависит от реализации.
        """
        # Default: try a simple GET with the token
        # Override in provider-specific subclasses
        try:
            resp = self._http.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                headers={"Authorization": f"Bearer {token.access_token}"},
            )
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

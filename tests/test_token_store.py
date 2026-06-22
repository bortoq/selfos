from __future__ import annotations

from selfos.config import create_profile, current_profile, profile_dir, set_current_profile
from selfos.integrations.token_store import OAuthToken, SecureTokenStore


def test_profile_helpers_create_and_switch_profiles() -> None:
    create_profile("work")
    set_current_profile("work")

    assert current_profile() == "work"
    assert profile_dir().name == "work"
    assert profile_dir("work").exists()


def test_token_store_plain_backend_uses_profile_directory() -> None:
    token = OAuthToken(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_at=12345.0,
    )
    store = SecureTokenStore(profile="work")
    store._backend = "plain"
    store.save("gmail", token)

    loaded = store.load("gmail")

    assert loaded is not None
    assert loaded.access_token == "access-token"
    assert store.list_providers() == ["gmail"]
    assert store._tokens_dir() == profile_dir("work") / "tokens"

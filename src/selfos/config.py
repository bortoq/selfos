"""
Конфигурация путей Self OS.

Все пути к данным теперь централизованы здесь.
По умолчанию: ~/.selfos/
Переопределяется через SELFOS_HOME.
"""

import os
from pathlib import Path
from typing import Any

import yaml


def _get_home() -> Path:
    """Возвращает корневую директорию Self OS."""
    return Path(os.getenv("SELFOS_HOME", Path.home() / ".selfos"))


def profiles_dir() -> Path:
    """Директория профилей."""
    return _get_home() / "profiles"


def current_profile_file() -> Path:
    """Файл с именем активного профиля."""
    return profiles_dir() / ".current_profile"


def current_profile() -> str:
    """Имя активного профиля."""
    path = current_profile_file()
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "default"


def _validate_profile_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Profile name cannot be empty")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if any(char not in allowed for char in cleaned):
        raise ValueError("Profile name may contain only letters, digits, '-' and '_'")
    return cleaned


def profile_dir(profile: str | None = None) -> Path:
    """Директория указанного или текущего профиля."""
    selected = _validate_profile_name(profile or current_profile())
    return profiles_dir() / selected


def create_profile(name: str) -> Path:
    """Создаёт профиль и базовые директории."""
    path = profile_dir(name)
    (path / "tokens").mkdir(parents=True, exist_ok=True)
    return path


def set_current_profile(name: str) -> str:
    """Переключает текущий профиль."""
    selected = _validate_profile_name(name)
    path = profile_dir(selected)
    if not path.exists():
        raise ValueError(f"Profile '{selected}' does not exist")
    current_path = current_profile_file()
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(selected, encoding="utf-8")
    return selected


def list_profiles() -> list[str]:
    """Список существующих профилей."""
    root = profiles_dir()
    if not root.exists():
        return []
    profiles = [item.name for item in root.iterdir() if item.is_dir()]
    return sorted(profiles)


def data_dir() -> Path:
    """Директория для Activity Log."""
    return _get_home() / "data" / "activity"


def trust_file() -> Path:
    """Файл счётчиков доверия."""
    return _get_home() / "data" / "trust.json"


def config_file() -> Path:
    """Файл конфигурации selfos.yaml."""
    # Сначала проверяем рядом с проектом, потом ~/.selfos/
    local = Path("selfos.yaml")
    if local.exists():
        return local
    return _get_home() / "selfos.yaml"


def media_dir() -> Path:
    """Директория для медиа-файлов."""
    return _get_home() / "media"


def plugins_dir() -> Path:
    """Директория для пользовательских плагинов."""
    return _get_home() / "plugins"


def rules_file() -> Path:
    """Файл пользовательских правил делегирования."""
    return _get_home() / "rules.yaml"


def rate_limits_file() -> Path:
    """Файл persistent rate limiter state."""
    return _get_home() / "rate_limits.json"


def llm_dir() -> Path:
    """Директория LLM state."""
    return _get_home() / "llm"


def prompts_dir() -> Path:
    """Директория user prompt templates."""
    return _get_home() / "prompts"


def llm_config() -> dict[str, Any]:
    """Возвращает конфигурацию llm из selfos.yaml."""
    path = config_file()
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        return {}
    llm = raw.get("llm", {})
    return llm if isinstance(llm, dict) else {}


def update_llm_config(values: dict[str, Any]) -> dict[str, Any]:
    """Обновляет раздел llm в selfos.yaml."""
    path = config_file()
    current: dict[str, Any] = {}
    if path.exists():
        with open(path, encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if isinstance(loaded, dict):
            current = loaded
    llm = current.get("llm", {})
    if not isinstance(llm, dict):
        llm = {}
    llm.update(values)
    current["llm"] = llm
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(current, handle, sort_keys=False, allow_unicode=True)
    return llm

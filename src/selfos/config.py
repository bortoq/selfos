"""
Конфигурация путей Self OS.

Все пути к данным теперь централизованы здесь.
По умолчанию: ~/.selfos/
Переопределяется через SELFOS_HOME.
"""

import os
from pathlib import Path


def _get_home() -> Path:
    """Возвращает корневую директорию Self OS."""
    return Path(os.getenv("SELFOS_HOME", Path.home() / ".selfos"))


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

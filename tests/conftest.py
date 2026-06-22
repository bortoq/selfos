from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_selfos_home(monkeypatch: pytest.MonkeyPatch, tmp_path: object) -> None:
    monkeypatch.setenv("SELFOS_HOME", str(tmp_path))

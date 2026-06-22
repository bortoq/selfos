"""Tests for trust manager with isolated tmp_path."""

from selfos import trust as trust_module
from selfos.trust import (
    can_auto,
    get_threshold,
    increase_trust,
    reset_trust,
)


def test_default_thresholds():
    """Проверяем, что пороги доверия возвращаются корректно"""
    assert get_threshold("event_categorization") == 10
    assert get_threshold("photo_classification") == 6
    assert get_threshold("quick_note") == 5


def test_increase_trust(monkeypatch, tmp_path):
    """Проверяем увеличение счётчика доверия"""
    monkeypatch.setattr(trust_module, "TRUST_FILE", tmp_path / "trust.json")
    reset_trust("test_action")
    count = increase_trust("test_action")
    assert count == 1

    count = increase_trust("test_action")
    assert count == 2

    reset_trust("test_action")


def test_can_auto(monkeypatch, tmp_path):
    """Проверяем логику перехода в auto-режим"""
    monkeypatch.setattr(trust_module, "TRUST_FILE", tmp_path / "trust.json")
    reset_trust("test_action")

    # По умолчанию порог = 10
    assert can_auto("test_action") is False

    # Делаем 10 успешных итераций
    for _ in range(10):
        increase_trust("test_action")

    assert can_auto("test_action") is True

    reset_trust("test_action")

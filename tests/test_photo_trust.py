"""Tests for photo classification trust integration."""

from scripts.photo_trust import classify_and_trust
from selfos import trust as trust_module
from selfos.trust import increase_trust, reset_trust


def test_classify_and_trust_review_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(trust_module, "TRUST_FILE", tmp_path / "trust.json")
    reset_trust("photo_classification")

    result = classify_and_trust("test.jpg", "food")
    assert result["status"] == "review"
    assert result["category"] == "food"


def test_classify_and_trust_auto_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(trust_module, "TRUST_FILE", tmp_path / "trust.json")
    reset_trust("photo_classification")

    # Делаем 6 успешных классификаций (порог = 6)
    for _ in range(6):
        increase_trust("photo_classification")

    result = classify_and_trust("lunch.jpg", "food")
    assert result["status"] == "auto"
    assert result["category"] == "food"

    reset_trust("photo_classification")

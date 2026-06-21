from scripts.smart_suggestions import generate_smart_suggestions


def test_smart_suggestions_returns_list():
    suggestions = generate_smart_suggestions()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_smart_suggestions_content():
    suggestions = generate_smart_suggestions()
    # Проверяем, что хотя бы одно предложение содержит ключевые слова
    text = " ".join(suggestions).lower()
    assert any(word in text for word in ["focus", "meeting", "work", "calm", "reflection"])
from src.selfos.context_engine import ContextEngine


def test_context_engine_empty():
    engine = ContextEngine(data_dir="nonexistent")
    patterns = engine.get_patterns()
    assert "message" in patterns


def test_context_engine_proactive_suggestions():
    engine = ContextEngine()
    suggestions = engine.get_proactive_suggestions()
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_context_engine_summary():
    engine = ContextEngine()
    summary = engine.get_context_summary()
    assert "Проанализировано" in summary or "событий" in summary
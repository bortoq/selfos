from src.selfos.delegation_engine import DelegationEngine


def test_critical_actions_never_auto():
    engine = DelegationEngine()
    assert engine.should_auto_execute("email_send") is False
    assert engine.should_auto_execute("delete_data") is False


def test_override_works():
    engine = DelegationEngine()
    engine.set_override("email_send", True)
    assert engine.should_auto_execute("email_send") is True
    engine.clear_override("email_send")
    assert engine.should_auto_execute("email_send") is False


def test_execute_blocked():
    engine = DelegationEngine()
    result = engine.execute("email_send", "quick_note", text="test")
    assert result["executed"] is False
    assert "not allowed" in result["reason"]
from selfos.unified_interface import UnifiedInterface


def test_unified_interface_register_and_execute():
    interface = UnifiedInterface()

    def dummy_handler(**kwargs):
        return {"message": "ok", "args": kwargs}

    interface.register_handler("test", dummy_handler)
    result = interface.execute("test", foo="bar")

    assert result["success"] is True
    assert result["result"]["message"] == "ok"


def test_unified_interface_unknown_command():
    interface = UnifiedInterface()
    result = interface.execute("nonexistent")

    assert result["success"] is False
    assert "Unknown command" in result["error"]
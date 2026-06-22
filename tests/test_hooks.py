"""
Тесты для hooks.py — система точек расширения ядра.
"""

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.hooks import (
    HookRegistry,
    get_hook_registry,
    reset_hook_registry,
    HOOK_BEFORE,
    HOOK_AFTER,
    HOOK_INSTEAD,
    HOOK_EMAIL_SEND,
    HOOK_NOTE_CREATE,
    HOOK_TASK_CREATE,
    ALL_HOOK_POINTS,
)


class TestHookRegistry:
    def test_subscribe_and_has(self) -> None:
        reg = HookRegistry()
        reg.subscribe(HOOK_NOTE_CREATE, "test-plugin", lambda: None)
        assert reg.has_subscribers(HOOK_NOTE_CREATE) is True
        assert reg.has_subscribers("nonexistent") is False

    def test_subscribe_invalid_type(self) -> None:
        import pytest
        reg = HookRegistry()
        with pytest.raises(ValueError, match="Invalid hook_type"):
            reg.subscribe(HOOK_NOTE_CREATE, "p", lambda: None, hook_type="magic")

    def test_unsubscribe(self) -> None:
        reg = HookRegistry()
        reg.subscribe(HOOK_NOTE_CREATE, "p1", lambda: None)
        reg.subscribe(HOOK_NOTE_CREATE, "p2", lambda: None)
        assert reg.has_subscribers(HOOK_NOTE_CREATE) is True
        reg.unsubscribe(HOOK_NOTE_CREATE, "p1")
        assert reg.has_subscribers(HOOK_NOTE_CREATE) is True  # p2 still there
        reg.unsubscribe(HOOK_NOTE_CREATE, "p2")
        assert reg.has_subscribers(HOOK_NOTE_CREATE) is False

    def test_unsubscribe_nonexistent(self) -> None:
        reg = HookRegistry()
        assert reg.unsubscribe(HOOK_NOTE_CREATE, "ghost") is False

    def test_unsubscribe_all(self) -> None:
        reg = HookRegistry()
        reg.subscribe(HOOK_NOTE_CREATE, "p", lambda: None)
        reg.subscribe(HOOK_TASK_CREATE, "p", lambda: None)
        count = reg.unsubscribe_all("p")
        assert count == 2
        assert reg.has_subscribers(HOOK_NOTE_CREATE) is False

    def test_trigger_before_modifies_context(self) -> None:
        reg = HookRegistry()
        def handler(**ctx):
            ctx["modified"] = True
            return ctx
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler, hook_type=HOOK_BEFORE)
        result = reg.trigger_before(HOOK_NOTE_CREATE, text="hello")
        assert result["modified"] is True
        assert result["text"] == "hello"

    def test_trigger_after_modifies_result(self) -> None:
        reg = HookRegistry()
        def handler(result, **ctx):
            result["modified"] = True
            return result
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler, hook_type=HOOK_AFTER)
        result = reg.trigger_after(HOOK_NOTE_CREATE, result={"original": True}, text="hi")
        assert result["original"] is True
        assert result["modified"] is True

    def test_trigger_after_no_subscribers(self) -> None:
        reg = HookRegistry()
        result = reg.trigger_after(HOOK_NOTE_CREATE, result={"x": 1})
        assert result == {"x": 1}

    def test_trigger_before_no_subscribers(self) -> None:
        reg = HookRegistry()
        result = reg.trigger_before(HOOK_NOTE_CREATE, x=1)
        assert result == {"x": 1}

    def test_trigger_instead_replaces(self) -> None:
        reg = HookRegistry()
        def handler(**ctx):
            return {"custom": True}
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler, hook_type=HOOK_INSTEAD)
        result = reg.trigger_instead(HOOK_NOTE_CREATE, text="hello")
        assert result == {"custom": True}

    def test_trigger_instead_no_subscribers(self) -> None:
        reg = HookRegistry()
        result = reg.trigger_instead(HOOK_NOTE_CREATE)
        assert result is None

    def test_trigger_instead_none_return_skips(self) -> None:
        reg = HookRegistry()
        def handler(**ctx):
            return None  # Instead handler returned None → skip
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler, hook_type=HOOK_INSTEAD)
        result = reg.trigger_instead(HOOK_NOTE_CREATE)
        assert result is None

    def test_multiple_before_handlers_chain(self) -> None:
        reg = HookRegistry()
        def add_a(**ctx):
            ctx["value"] = ctx.get("value", "") + "A"
            return ctx
        def add_b(**ctx):
            ctx["value"] = ctx.get("value", "") + "B"
            return ctx
        reg.subscribe(HOOK_NOTE_CREATE, "a", add_a, hook_type=HOOK_BEFORE)
        reg.subscribe(HOOK_NOTE_CREATE, "b", add_b, hook_type=HOOK_BEFORE)
        result = reg.trigger_before(HOOK_NOTE_CREATE, value="")
        # Both handlers run (order depends on registration)
        assert "A" in result["value"]
        assert "B" in result["value"]

    def test_list_subscriptions(self) -> None:
        reg = HookRegistry()
        reg.subscribe(HOOK_NOTE_CREATE, "p1", lambda: None, hook_type=HOOK_BEFORE)
        reg.subscribe(HOOK_NOTE_CREATE, "p2", lambda: None, hook_type=HOOK_AFTER)
        subs = reg.list_subscriptions()
        assert HOOK_NOTE_CREATE in subs
        assert len(subs[HOOK_NOTE_CREATE]) == 2

    def test_list_subscriptions_filtered(self) -> None:
        reg = HookRegistry()
        reg.subscribe(HOOK_NOTE_CREATE, "p", lambda: None)
        reg.subscribe(HOOK_TASK_CREATE, "p", lambda: None)
        subs = reg.list_subscriptions(hook_point=HOOK_NOTE_CREATE)
        assert HOOK_NOTE_CREATE in subs
        assert HOOK_TASK_CREATE not in subs

    def test_handler_exception_does_not_crash(self) -> None:
        reg = HookRegistry()
        def crashing_handler(**ctx):
            raise RuntimeError("oops")
        reg.subscribe(HOOK_NOTE_CREATE, "p", crashing_handler, hook_type=HOOK_BEFORE)
        # Should not raise
        result = reg.trigger_before(HOOK_NOTE_CREATE, text="safe")
        assert result["text"] == "safe"

    def test_subscribe_replaces_existing(self) -> None:
        """Re-subscribing the same plugin replaces old handler."""
        reg = HookRegistry()
        results = []
        def handler1(**ctx):
            results.append("h1")
            return ctx
        def handler2(**ctx):
            results.append("h2")
            return ctx
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler1, hook_type=HOOK_BEFORE)
        reg.subscribe(HOOK_NOTE_CREATE, "p", handler2, hook_type=HOOK_BEFORE)
        reg.trigger_before(HOOK_NOTE_CREATE)
        # Only handler2 should be called (handler1 replaced)
        assert results == ["h2"]


class TestGlobalRegistry:
    def test_get_and_reset(self) -> None:
        reset_hook_registry()
        r1 = get_hook_registry()
        r2 = get_hook_registry()
        assert r1 is r2  # Same instance
        reset_hook_registry()
        r3 = get_hook_registry()
        assert r3 is not r1  # New instance after reset


class TestHookPointConstants:
    def test_all_hook_points_defined(self) -> None:
        assert len(ALL_HOOK_POINTS) >= 10  # At least 10 hook points
        assert HOOK_NOTE_CREATE in ALL_HOOK_POINTS
        assert HOOK_EMAIL_SEND in ALL_HOOK_POINTS


class TestPluginOnRegister:
    """Test that on_register is called during PluginRegistry.register()."""

    def test_on_register_called(self) -> None:
        from selfos.plugin_registry import PluginRegistry
        from selfos.hooks import reset_hook_registry, get_hook_registry

        reset_hook_registry()
        reg = PluginRegistry()
        hook_reg = get_hook_registry()

        registered_hooks = []

        class HookTestPlugin(BaseSelfOSPlugin):
            name = "hook-test"
            description = "Test"
            version = "1.0.0"
            def execute(self, **kwargs):
                return {"result": "ok"}
            def on_register(self, hr):
                registered_hooks.append(True)
                hr.subscribe("note:create", self.name, lambda **x: x, hook_type="before")

        reg.register("hook-test", HookTestPlugin)
        assert len(registered_hooks) == 1
        assert hook_reg.has_subscribers("note:create") is True

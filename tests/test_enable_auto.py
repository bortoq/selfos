import yaml

from selfos.plugin_registry import PluginRegistry


def test_enable_auto(tmp_path, monkeypatch):
    import plugins.enable_auto_plugin as ea_plugin
    config_path = tmp_path / "selfos.yaml"
    config_path.write_text(
        yaml.dump({"force_review": {"event_categorization": True}})
    )
    monkeypatch.setattr(ea_plugin, "config_file", lambda: config_path)

    plugin = PluginRegistry.get_plugin("enable_auto")
    plugin.execute(action="event_categorization", enable=True)

    new_config = yaml.safe_load(config_path.read_text())
    assert new_config["force_review"]["event_categorization"] is False


def test_disable_auto(tmp_path, monkeypatch):
    import plugins.enable_auto_plugin as ea_plugin
    config_path = tmp_path / "selfos.yaml"
    config_path.write_text(
        yaml.dump({"force_review": {}})
    )
    monkeypatch.setattr(ea_plugin, "config_file", lambda: config_path)

    plugin = PluginRegistry.get_plugin("enable_auto")
    plugin.execute(action="event_categorization", enable=False)

    new_config = yaml.safe_load(config_path.read_text())
    assert new_config["force_review"]["event_categorization"] is True
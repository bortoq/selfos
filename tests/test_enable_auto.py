import yaml

from scripts.enable_auto import disable_auto, enable_auto


def test_enable_auto(tmp_path, monkeypatch):
    # Создаём временный конфиг
    config_path = tmp_path / "selfos.yaml"
    config = {"force_review": {"event_categorization": True}}
    config_path.write_text(yaml.dump(config))

    monkeypatch.chdir(tmp_path)

    enable_auto("event_categorization")

    new_config = yaml.safe_load(config_path.read_text())
    assert new_config["force_review"]["event_categorization"] is False


def test_disable_auto(tmp_path, monkeypatch):
    config_path = tmp_path / "selfos.yaml"
    config = {"force_review": {}}
    config_path.write_text(yaml.dump(config))

    monkeypatch.chdir(tmp_path)

    disable_auto("event_categorization")

    new_config = yaml.safe_load(config_path.read_text())
    assert new_config["force_review"]["event_categorization"] is True
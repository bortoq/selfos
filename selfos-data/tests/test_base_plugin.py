import pytest
from plugins.base_plugin import BasePlugin


def test_base_plugin_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BasePlugin()


def test_base_plugin_methods_exist():
    # Проверяем, что класс имеет необходимые методы
    assert hasattr(BasePlugin, "fetch")
    assert hasattr(BasePlugin, "push")
    assert hasattr(BasePlugin, "validate_config")
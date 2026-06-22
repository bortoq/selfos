"""
Plugin SDK — инструментарий для создания плагинов Self OS.

Упрощает разработку, упаковку и публикацию плагинов.
"""

from typing import Any

from selfos.base_selfos_plugin import BaseSelfOSPlugin
from selfos.plugin_contracts import (
    CategorizerPlugin,
    NotingPlugin,
    SmartSuggestPlugin,
    SummarizerPlugin,
)
from selfos.plugin_manifest import PluginManifest

# Registry of known protocols for validation
KNOWN_PROTOCOLS: dict[str, type] = {
    "NotingPlugin": NotingPlugin,
    "CategorizerPlugin": CategorizerPlugin,
    "SummarizerPlugin": SummarizerPlugin,
    "SmartSuggestPlugin": SmartSuggestPlugin,
}



def create_plugin(
    name: str,
    execute_fn: Any,
    *,
    description: str = "",
    version: str = "0.1.0",
    author: str = "Unknown",
    protocol: str = "",
    dependencies: list[str] | None = None,
) -> type[BaseSelfOSPlugin]:
    """
    Создаёт класс плагина из функции.

    Это самый быстрый способ создать плагин без написания boilerplate.

    Пример:
        def my_handler(text: str, **kwargs) -> dict:
            return {"result": f"Hello {text}"}

        MyPlugin = create_plugin("greeter", my_handler,
            description="Greets the user",
            protocol="NotingPlugin",
        )
        PluginRegistry.get_instance().register("greeter", MyPlugin)
    """
    deps = dependencies or []

    # Динамически создаём класс, наследующий BaseSelfOSPlugin
    plugin_class = type(
        name.title().replace("-", "").replace("_", "") + "Plugin",
        (BaseSelfOSPlugin,),
        {
            "name": name,
            "description": description or name,
            "version": version,
            "author": author,
            "dependencies": deps,
            "protocol": protocol,
            "execute": execute_fn,
            "__module__": "__selfos_plugin__",
        },
    )
    return plugin_class


def validate_plugin(plugin_class: type) -> list[str]:
    """
    Проверяет, что класс плагина соответствует контракту.

    Возвращает список ошибок (пустой список = плагин корректен).
    """
    errors: list[str] = []

    if not issubclass(plugin_class, BaseSelfOSPlugin):
        errors.append("Plugin must inherit from BaseSelfOSPlugin")
        return errors

    if not hasattr(plugin_class, "execute"):
        errors.append("Plugin must have an execute() method")
    elif not callable(plugin_class.execute):
        errors.append("Plugin.execute() must be callable")

    name = getattr(plugin_class, "name", "")
    if not name:
        errors.append("Plugin must have a non-empty 'name' attribute")

    return errors


def scaffold_plugin(
    name: str,
    dest_dir: str,
    *,
    author: str = "",
    description: str = "",
    protocol: str = "",
) -> list[str]:
    """
    Создаёт файлы нового плагина в dest_dir.

    Returns:
        Список созданных файлов.
    """
    import os

    dest = os.path.abspath(dest_dir)
    os.makedirs(dest, exist_ok=True)

    safe_name = name.replace("-", "_").lower()
    class_name = "".join(part.title() for part in safe_name.split("_")) + "Plugin"

    files_created: list[str] = []

    # plugin.yaml
    manifest = PluginManifest(
        name=name,
        version="0.1.0",
        description=description or f"{name} plugin for Self OS",
        author=author or "Unknown",
        entry_point=f"{safe_name}.{safe_name}:{class_name}",
        protocol=protocol,
    )
    manifest_path = os.path.join(dest, "plugin.yaml")
    with open(manifest_path, "w") as f:
        f.write(manifest.to_yaml())
    files_created.append(manifest_path)

    # __init__.py
    init_path = os.path.join(dest, "__init__.py")
    with open(init_path, "w") as f:
        f.write(f'"""Plugin: {name}."""\n')
    files_created.append(init_path)

    # plugin code
    plugin_path = os.path.join(dest, f"{safe_name}.py")
    protocol_import = ""
    protocol_hint = ""
    if protocol and protocol in KNOWN_PROTOCOLS:
        protocol_import = (
            f"from selfos.plugin_contracts import {protocol}"
        )
        protocol_hint = (
            f"\n\n"
            f"# Этот плагин реализует protocol {protocol}:\n"
            f"# assert isinstance(instance, {protocol})\n"
        )

    code = f'''"""
{name} — плагин для Self OS.
"""

from selfos.base_selfos_plugin import BaseSelfOSPlugin
{protocol_import}


class {class_name}(BaseSelfOSPlugin):
    name = "{safe_name}"
    description = "{description or name} plugin"
    version = "{manifest.version}"
    author = "{author or "Unknown"}"
    dependencies: list[str] = []
    protocol = "{protocol}"
{protocol_hint}
    def execute(self, **kwargs):
        """
        Основная логика плагина.
        """
        return {{"result": "ok"}}
'''
    with open(plugin_path, "w") as f:
        f.write(code)
    files_created.append(plugin_path)

    return files_created

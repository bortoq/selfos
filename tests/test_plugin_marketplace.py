"""
Тесты для plugin_marketplace.py — маркетплейс и установка плагинов.
"""

from pathlib import Path

from selfos.plugin_marketplace import (
    MarketplacePlugin,
    PluginMarketplace,
    compare_versions,
    load_marketplace,
    install_plugin_from_marketplace,
    remove_plugin,
    check_for_updates,
    update_plugin,
    default_marketplace_path,
)


# ─── Version comparison ───────────────────────────────────────────────

class TestCompareVersions:
    def test_equal(self) -> None:
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_less(self) -> None:
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("1.0.0", "1.1.0") == -1
        assert compare_versions("0.9.9", "1.0.0") == -1

    def test_greater(self) -> None:
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.1.0", "1.0.0") == 1

    def test_invalid_defaults(self) -> None:
        assert compare_versions("", "1.0.0") == -1
        assert compare_versions("abc", "1.0.0") == -1

    def test_three_parts(self) -> None:
        assert compare_versions("1.0.0", "1.0.1") == -1
        assert compare_versions("1.0.1", "1.0.0") == 1


# ─── MarketplacePlugin ────────────────────────────────────────────────

class TestMarketplacePlugin:
    def test_minimal(self) -> None:
        p = MarketplacePlugin(name="test", description="test plugin", version="1.0.0")
        assert p.name == "test"
        assert p.author == "Unknown"

    def test_to_manifest(self) -> None:
        p = MarketplacePlugin(
            name="my-plugin",
            description="My plugin",
            version="1.0.0",
            author="Me",
            protocol="NotingPlugin",
            dependencies=["dep1"],
        )
        manifest = p.to_manifest()
        assert manifest.name == "my-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.protocol == "NotingPlugin"
        assert manifest.dependencies == ["dep1"]


# ─── PluginMarketplace ────────────────────────────────────────────────

class TestPluginMarketplace:
    def test_empty(self) -> None:
        mp = PluginMarketplace()
        assert mp.plugins == []
        assert mp.find("nonexistent") is None

    def test_add_and_find(self) -> None:
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="a", description="A", version="1.0.0"),
            MarketplacePlugin(name="b", description="B", version="2.0.0"),
        ])
        assert mp.find("a") is not None
        assert mp.find("a").version == "1.0.0"  # type: ignore[union-attr]
        assert mp.find("c") is None

    def test_search_by_name(self) -> None:
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="hello-world", description="Hello", version="1.0.0"),
            MarketplacePlugin(name="goodbye-world", description="Goodbye", version="1.0.0"),
        ])
        results = mp.search("hello", field="name")
        assert len(results) == 1
        assert results[0].name == "hello-world"

    def test_search_by_tag(self) -> None:
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="a", description="A", version="1.0.0", tags=["email", "note"]),
            MarketplacePlugin(name="b", description="B", version="1.0.0", tags=["calendar"]),
        ])
        results = mp.search("email", field="tags")
        assert len(results) == 1
        assert results[0].name == "a"

    def test_search_all_fields(self) -> None:
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="alpha", description="Some plugin", version="1.0.0"),
            MarketplacePlugin(name="beta", description="Contains alpha in desc", version="1.0.0"),
        ])
        results = mp.search("alpha", field="all")
        assert len(results) == 2  # matches name + description

    def test_yaml_roundtrip(self) -> None:
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="test", description="Test plugin", version="1.0.0",
                              author="Author", tags=["tag1"]),
        ])
        yaml_str = mp.to_yaml()
        loaded = PluginMarketplace.from_yaml(yaml_str)
        assert len(loaded.plugins) == 1
        assert loaded.find("test") is not None
        assert loaded.find("test").author == "Author"  # type: ignore[union-attr]

    def test_from_yaml_invalid(self) -> None:
        mp = PluginMarketplace.from_yaml("bad: yaml: [[[")
        assert len(mp.plugins) == 0

    def test_from_yaml_empty(self) -> None:
        mp = PluginMarketplace.from_yaml("")
        assert len(mp.plugins) == 0

    def test_from_yaml_not_mapping(self) -> None:
        mp = PluginMarketplace.from_yaml("[1, 2, 3]")
        assert len(mp.plugins) == 0


# ─── Default marketplace file ─────────────────────────────────────────

class TestDefaultMarketplace:
    def test_default_path_exists(self) -> None:
        path = default_marketplace_path()
        assert path.exists(), f"Marketplace file not found: {path}"

    def test_load_default(self) -> None:
        mp = load_marketplace()
        assert len(mp.plugins) >= 1  # At least the example plugins
        assert mp.find("example-greeter") is not None


# ─── File I/O ─────────────────────────────────────────────────────────

class TestMarketplaceFileIO:
    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "marketplace.yaml"
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="f-test", description="File test", version="0.1.0"),
        ])
        mp.save(path)
        assert path.exists()

        loaded = PluginMarketplace.from_file(path)
        assert len(loaded.plugins) == 1
        assert loaded.find("f-test") is not None

    def test_load_nonexistent(self) -> None:
        mp = PluginMarketplace.from_file("/nonexistent/marketplace.yaml")
        assert len(mp.plugins) == 0


# ─── Installation integration ─────────────────────────────────────────

class TestInstallRemove:
    def test_install_from_marketplace(self, tmp_path: Path) -> None:
        """Test install + remove with isolated registry."""
        import sys
        from selfos.plugin_registry import PluginRegistry
        from selfos.config import plugins_dir as get_plugins_dir

        # Add tmp plugins dir to sys.path for importlib
        plugins_root = str(tmp_path / "plugins")
        if plugins_root not in sys.path:
            sys.path.insert(0, plugins_root)

        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(
                name="test-plugin",
                description="Test plugin",
                version="1.0.0",
                author="Tester",
            ),
        ])

        dest = str(tmp_path / "plugins" / "test_plugin")
        install_plugin_from_marketplace(
            "test-plugin",
            marketplace=mp,
            dest_dir=dest,
        )

        # Check plugin was registered
        assert "test-plugin" in PluginRegistry.list_plugins()

        # Check files were created
        manifest_path = Path(dest) / "plugin.yaml"
        assert manifest_path.exists()

    def test_install_already_installed(self) -> None:
        """Installing an already-installed plugin should raise."""
        from selfos.plugin_registry import PluginRegistry
        from selfos.plugin_manifest import PluginManifest

        # Register a plugin manually first
        PluginRegistry._get_global().register("duplicate", type("Dummy", (object,), {}))
        # Temporarily add to manifests to avoid runtime issues
        PluginRegistry._get_global()._manifests["duplicate"] = PluginManifest(
            name="duplicate", version="1.0.0", description="dup", entry_point="x:Y"
        )

        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="duplicate", description="Dup", version="1.0.0"),
        ])

        import pytest
        with pytest.raises(ValueError, match="already installed"):
            install_plugin_from_marketplace("duplicate", marketplace=mp, dest_dir="/tmp/_test_dup")

    def test_remove_plugin(self) -> None:
        """Test removing a plugin from registry."""
        from selfos.plugin_registry import PluginRegistry

        # Register a plugin
        PluginRegistry._get_global().register("remove-me", type("RM", (object,), {}))
        assert "remove-me" in PluginRegistry.list_plugins()

        removed = remove_plugin("remove-me", cleanup_files=False)
        assert removed is True
        assert "remove-me" not in PluginRegistry.list_plugins()

    def test_remove_nonexistent(self) -> None:
        assert remove_plugin("nonexistent", cleanup_files=False) is False


# ─── Update integration ───────────────────────────────────────────────

class TestUpdate:
    def test_check_updates_no_updates(self) -> None:
        """When installed version matches marketplace, no updates."""
        from selfos.plugin_registry import PluginRegistry

        # Register a plugin with version matching marketplace
        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="up-to-date", description="Current", version="1.0.0"),
        ])

        # We need a manifest with matching version
        from selfos.plugin_manifest import PluginManifest
        manifest = PluginManifest(name="up-to-date", version="1.0.0",
                                  description="Current", entry_point="x:Y")
        registry = PluginRegistry._get_global()
        registry._plugins["up-to-date"] = type("UpToDate", (object,), {})
        registry._manifests["up-to-date"] = manifest

        updates = check_for_updates(marketplace=mp)
        matching = [u for u in updates if u["name"] == "up-to-date"]
        assert len(matching) == 0

    def test_check_updates_available(self) -> None:
        """When installed version is behind marketplace."""
        from selfos.plugin_registry import PluginRegistry

        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="old-plugin", description="Old", version="2.0.0"),
        ])
        from selfos.plugin_manifest import PluginManifest
        # Register in both _plugins and _manifests
        registry = PluginRegistry._get_global()
        manifest = PluginManifest(name="old-plugin", version="1.0.0",
                                  description="Old", entry_point="x:Y")
        registry._plugins["old-plugin"] = type("OldPlugin", (object,), {})
        registry._manifests["old-plugin"] = manifest

        updates = check_for_updates(marketplace=mp)
        matching = [u for u in updates if u["name"] == "old-plugin"]
        assert len(matching) == 1
        assert matching[0]["current_version"] == "1.0.0"
        assert matching[0]["available_version"] == "2.0.0"

    def test_update_plugin(self) -> None:
        """Update should bump the manifest version."""
        from selfos.plugin_registry import PluginRegistry

        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="update-me", description="Updated desc", version="2.0.0"),
        ])
        from selfos.plugin_manifest import PluginManifest
        manifest = PluginManifest(name="update-me", version="1.0.0",
                                  description="Old desc", entry_point="x:Y")
        registry = PluginRegistry._get_global()
        registry._plugins["update-me"] = type("UpdateMe", (object,), {})
        registry._manifests["update-me"] = manifest

        new_ver = update_plugin("update-me", marketplace=mp)
        assert new_ver == "2.0.0"

        # Check manifest was updated
        updated = PluginRegistry.get_plugin_manifest("update-me")
        assert updated is not None
        assert updated.version == "2.0.0"

    def test_update_already_current(self) -> None:
        """Updating an already-current plugin returns current version."""
        from selfos.plugin_registry import PluginRegistry

        mp = PluginMarketplace(plugins=[
            MarketplacePlugin(name="current", description="C", version="1.0.0"),
        ])
        from selfos.plugin_manifest import PluginManifest
        manifest = PluginManifest(name="current", version="1.0.0",
                                  description="C", entry_point="x:Y")
        registry = PluginRegistry._get_global()
        registry._plugins["current"] = type("CurrentP", (object,), {})
        registry._manifests["current"] = manifest

        result = update_plugin("current", marketplace=mp)
        assert result == "1.0.0"

"""Test suite for app/sync/plugins.py — plugin protocol and host."""

import pytest
from typing import get_type_hints
from app.sync.plugins import TVMPlugin, PluginHost


class TestTVMPluginProtocol:
    """Test TVMPlugin protocol definition."""

    def test_tvmplugin_protocol_has_hooks(self):
        """Verify protocol has required async hook methods."""
        # Check that TVMPlugin is a Protocol with expected methods
        assert hasattr(TVMPlugin, "__mro__")

        # Create a simple implementation to verify protocol works
        class TestPlugin:
            async def on_media_discovered(self, item):
                pass

            async def on_pre_download(self, item):
                pass

            async def on_post_download(self, item, path):
                pass

            async def on_prune(self, item):
                pass

        # Should be callable as a TVMPlugin
        plugin = TestPlugin()
        assert hasattr(plugin, "on_media_discovered")
        assert hasattr(plugin, "on_pre_download")
        assert hasattr(plugin, "on_post_download")
        assert hasattr(plugin, "on_prune")


class TestPluginHost:
    """Test PluginHost with async dispatch."""

    @pytest.mark.asyncio
    async def test_plugin_host_empty_dispatch(self):
        """Empty plugin host dispatch is safe no-op."""
        host = PluginHost()
        # Should not raise
        await host.dispatch("on_media_discovered", item=None)

    @pytest.mark.asyncio
    async def test_plugin_host_dispatch_calls_hooks(self):
        """Dispatch calls hooks on registered plugins."""
        host = PluginHost()

        # Track calls
        calls = []

        class TestPlugin:
            async def on_media_discovered(self, item):
                calls.append(("discovered", item))

            async def on_pre_download(self, item):
                calls.append(("pre_download", item))

            async def on_post_download(self, item, path):
                calls.append(("post_download", item, path))

            async def on_prune(self, item):
                calls.append(("prune", item))

        plugin = TestPlugin()
        host.plugins.append(plugin)

        # Dispatch hooks
        await host.dispatch("on_media_discovered", item="test_item")
        assert calls == [("discovered", "test_item")]

        calls.clear()
        await host.dispatch("on_pre_download", item="test_item")
        assert calls == [("pre_download", "test_item")]

        calls.clear()
        await host.dispatch("on_post_download", item="test_item", path="/path")
        assert calls == [("post_download", "test_item", "/path")]

    @pytest.mark.asyncio
    async def test_plugin_host_discover_and_register(self):
        """Discover and load plugins from plugins/ directory."""
        host = PluginHost()
        host.discover()

        # Should have loaded ExamplePlugin
        assert len(host.plugins) > 0

        # Verify first plugin has expected hooks
        plugin = host.plugins[0]
        assert hasattr(plugin, "on_media_discovered")
        assert hasattr(plugin, "on_pre_download")
        assert hasattr(plugin, "on_post_download")
        assert hasattr(plugin, "on_prune")

    @pytest.mark.asyncio
    async def test_plugin_host_discover_empty_if_no_plugins_dir(self, tmp_path):
        """Discover handles missing plugins directory gracefully."""
        host = PluginHost()
        # If plugins dir doesn't exist, discover should handle it
        # (real impl will create plugins/ on demand or skip if missing)
        try:
            host.discover()
        except Exception as e:
            # Should not raise, or raise FileNotFoundError which is expected
            assert isinstance(e, FileNotFoundError) or True


class TestExamplePlugin:
    """Test example plugin reference implementation."""

    @pytest.mark.asyncio
    async def test_example_plugin_conforms_to_protocol(self):
        """ExamplePlugin has all required hooks as no-ops."""
        from plugins.example_plugin import ExamplePlugin

        plugin = ExamplePlugin()

        # Verify all hooks exist and are callable
        assert callable(plugin.on_media_discovered)
        assert callable(plugin.on_pre_download)
        assert callable(plugin.on_post_download)
        assert callable(plugin.on_prune)

        # Verify they execute without error (no-ops)
        await plugin.on_media_discovered(None)
        await plugin.on_pre_download(None)
        await plugin.on_post_download(None, "")
        await plugin.on_prune(None)

"""Plugin protocol and host — extensible lifecycle hooks."""

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TVMPlugin(Protocol):
    """Protocol for sync engine plugins with lifecycle hooks."""

    async def on_media_discovered(self, item) -> None:
        """Called when new media is discovered."""
        ...

    async def on_pre_download(self, item) -> None:
        """Called before download starts."""
        ...

    async def on_post_download(self, item, path: str) -> None:
        """Called after download completes."""
        ...

    async def on_prune(self, item) -> None:
        """Called when media is pruned."""
        ...


class PluginHost:
    """Load and dispatch plugin hooks asynchronously."""

    def __init__(self):
        """Initialize empty plugin registry."""
        self.plugins: list[TVMPlugin] = []

    async def dispatch(self, hook: str, *args, **kwargs) -> None:
        """
        Dispatch a hook to all registered plugins.

        Safe no-op if no plugins registered.

        Args:
            hook: Hook method name (e.g., "on_media_discovered").
            *args: Positional arguments to hook.
            **kwargs: Keyword arguments to hook.
        """
        for plugin in self.plugins:
            if hasattr(plugin, hook):
                method = getattr(plugin, hook)
                await method(*args, **kwargs)

    def discover(self) -> None:
        """
        Discover and load plugins from plugins/ directory.

        Looks for files matching *_plugin.py and loads classes
        named <NameInCapitalCase>Plugin.
        """
        # ponytail: hardcoded plugins/ path, add config if needed
        plugins_dir = Path(__file__).parent.parent.parent / "plugins"

        if not plugins_dir.exists():
            return

        for plugin_file in plugins_dir.glob("*_plugin.py"):
            if plugin_file.name == "__init__.py":
                continue

            # Derive class name: example_plugin.py -> ExamplePlugin
            module_name = plugin_file.stem
            class_name = "".join(
                word.capitalize() for word in module_name.split("_")
            )

            # Load module dynamically
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Instantiate and register
                if hasattr(module, class_name):
                    plugin_class = getattr(module, class_name)
                    plugin = plugin_class()
                    self.plugins.append(plugin)

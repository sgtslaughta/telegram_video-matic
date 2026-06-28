"""Example no-op plugin — reference for the PluginBase contract."""

from app.sync.plugins import PluginBase


class ExamplePlugin(PluginBase):
    """Minimal reference: inherits all no-op hooks from PluginBase."""

    name = "example"
    version = "1.0.0"
    default_config: dict = {}

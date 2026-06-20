"""Example no-op plugin reference implementation."""


class ExamplePlugin:
    """Minimal reference implementation of TVMPlugin protocol."""

    async def on_media_discovered(self, item):
        """Called when media is discovered."""
        pass

    async def on_pre_download(self, item):
        """Called before download."""
        pass

    async def on_post_download(self, item, path):
        """Called after download."""
        pass

    async def on_prune(self, item):
        """Called when media is pruned."""
        pass

import pytest
from app.telegram.fast_telethon import download_file


def test_download_file_is_callable():
    """Smoke test: download_file exists and is callable."""
    assert callable(download_file)

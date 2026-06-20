"""Test suite for app/sync/naming.py — season/episode detection and path rendering."""

import pytest
from app.sync.naming import detect_season_episode, render_path


class TestDetectSeasonEpisode:
    """Test detect_season_episode() with ordered regex patterns."""

    def test_detect_season_episode_s01e02(self):
        """Detect S01E02 format."""
        assert detect_season_episode("Foo.S01E02.mkv") == (1, 2)

    def test_detect_season_episode_1x02(self):
        """Detect 1x02 format."""
        assert detect_season_episode("Show.1x02.mkv") == (1, 2)

    def test_detect_season_episode_season_n_episode_n(self):
        """Detect Season N Episode N format."""
        assert detect_season_episode("Season 2 Episode 5") == (2, 5)

    def test_detect_season_episode_fallback(self):
        """Fallback to (1, 1) for no match."""
        assert detect_season_episode("Random Movie.mkv") == (1, 1)

    def test_detect_season_episode_none_input(self):
        """Handle None input."""
        assert detect_season_episode(None) == (1, 1)

    def test_detect_season_episode_empty_string(self):
        """Handle empty string."""
        assert detect_season_episode("") == (1, 1)


class TestRenderPath:
    """Test render_path() with token interpolation."""

    def test_render_path_basic_tokens(self):
        """Render basic tokens."""
        result = render_path(
            "{channel}/{topic}/{title}{ext}",
            {"channel": "HBO", "topic": "series", "title": "Game", "ext": ".mkv"},
        )
        assert result == "HBO/series/Game.mkv"

    def test_render_path_season_episode_format(self):
        """Render with season/episode format specifiers (02d)."""
        result = render_path(
            "Show/Season {season:02d}/Show - S{season:02d}E{episode:02d}{ext}",
            {"season": 1, "episode": 2, "ext": ".mkv"},
        )
        assert result == "Show/Season 01/Show - S01E02.mkv"

    def test_render_path_missing_token_fallback_to_original(self):
        """Fallback to {original} when token missing."""
        result = render_path(
            "{channel}/{title}{ext}",
            {"original": "MyFile.mkv"},
        )
        assert result == "MyFile.mkv"

    def test_render_path_date_format(self):
        """Token date is string, not datetime."""
        result = render_path(
            "Archive/{date}/{title}{ext}",
            {"date": "2026-01-15", "title": "Show", "ext": ".mkv"},
        )
        assert result == "Archive/2026-01-15/Show.mkv"

    def test_render_path_all_tokens(self):
        """Render with all supported tokens."""
        result = render_path(
            "{channel}/{topic}/Season {season:02d}/{title} - S{season:02d}E{episode:02d}.{date}{ext}",
            {
                "channel": "HBO",
                "topic": "Drama",
                "season": 3,
                "episode": 7,
                "title": "Series",
                "date": "2026-06-20",
                "ext": ".mkv",
            },
        )
        assert result == "HBO/Drama/Season 03/Series - S03E07.2026-06-20.mkv"

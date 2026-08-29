"""Test suite for app/sync/naming.py — season/episode detection and path rendering."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from app.sync.naming import choose_target_path, detect_season_episode, render_path


def _item(file_name=None, caption=None):
    return SimpleNamespace(
        file_name=file_name, caption=caption, tg_msg_id=42,
        date_posted=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )


def _sub(template, season_detection=True, topic=None):
    return SimpleNamespace(
        rename_template=template, season_detection=season_detection, name="Sub",
        channel=SimpleNamespace(title="Rugby HD"),
        topic=SimpleNamespace(title=topic) if topic else None,
    )


class TestChooseTargetPath:
    """choose_target_path() decides template-vs-original and merges plugin tokens."""

    def test_template_without_se_tokens_applies_without_pattern(self):
        """A {channel}/{title} template needs no S##E## marker to render."""
        path, season, ep, used = choose_target_path(
            _item("match.mp4"), _sub("{channel}/{title}{ext}"), {})
        assert path == "Rugby HD/match.mp4" and used is True and season is None

    def test_topic_template_beats_channel_without_pattern(self):
        """Regression: unmatched rugby fell back to the channel folder, ignoring
        the subscription's {topic} template."""
        path, _s, _e, used = choose_target_path(
            _item("2026 08 15 Bulls [Pretoria].mp4"),
            _sub("{topic}/{title}.{ext}", topic="Summer Internationals"), {})
        assert path == "Summer Internationals/2026 08 15 Bulls [Pretoria].mp4"
        assert used is True

    def test_no_template_falls_back_to_topic_folder(self):
        path, _s, _e, used = choose_target_path(
            _item("game.mp4"), _sub(None, topic="Six Nations 2026"), {})
        assert path == "Six Nations 2026/game.mp4" and used is False

    def test_no_template_no_topic_falls_back_to_channel(self):
        path, _s, _e, used = choose_target_path(_item("game.mp4"), _sub(None), {})
        assert path == "Rugby HD/game.mp4" and used is False

    def test_se_template_without_pattern_keeps_original(self):
        """A {season}/{episode} template still needs a detected pattern."""
        path, _s, _e, used = choose_target_path(
            _item("no markers.mp4"),
            _sub("S{season:02d}E{episode:02d}{ext}", topic="URC"), {})
        assert path == "URC/no markers.mp4" and used is False

    def test_season_episode_uses_template(self):
        path, season, ep, used = choose_target_path(
            _item("Show.S02E05.mp4"), _sub("S{season:02d}E{episode:02d}{ext}"), {})
        assert path == "S02E05.mp4" and (season, ep) == (2, 5) and used is True

    def test_extra_tokens_force_template_without_pattern(self):
        """Plugin-supplied tokens (rugby) trigger the template even with no S/E."""
        extra = {"rugby_league": "Prem", "home": "Sale", "away": "Gloucester"}
        path, season, ep, used = choose_target_path(
            _item("sale v glos.mp4"),
            _sub("{rugby_league}/{home} vs {away}{ext}"),
            extra,
        )
        assert path == "Prem/Sale vs Gloucester.mp4" and used is True

    def test_extra_tokens_work_even_if_season_detection_off(self):
        extra = {"home": "Bath", "away": "Sale"}
        path, _s, _e, used = choose_target_path(
            _item("x.mp4"), _sub("{home}-{away}{ext}", season_detection=False), extra)
        assert path == "Bath-Sale.mp4" and used is True

    def test_se_pattern_ignored_when_season_detection_off(self):
        """season_detection off = no S/E parsing, but a pattern-free template
        still renders (season/episode stay None)."""
        path, season, ep, used = choose_target_path(
            _item("Show.S01E01.mp4"), _sub("{title}{ext}", season_detection=False), {})
        assert path == "Show.S01E01.mp4" and used is True
        assert (season, ep) == (None, None)


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

    def test_render_path_collapses_doubled_dot_extension(self):
        """A '{title}.{ext}' template (ext already has the dot) must not yield '..'."""
        result = render_path(
            "{channel}/{title}.{ext}",
            {"channel": "Ch", "title": "Match", "ext": ".mp4"},
        )
        assert result == "Ch/Match.mp4"

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

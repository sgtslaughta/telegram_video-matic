import pytest
from app.rugby.scraper import (
    parse_league_catalog,
    load_seed,
    RugbyScrapeError,
)


class TestParseLeagueCatalog:
    def test_parse_two_leagues_from_html(self):
        """Test parsing two league links from HTML snippet."""
        html = """
        <html>
        <body>
        <a href="/season/4414-english-prem-rugby/2025-2026">English Prem Rugby</a>
        <a href="/league/4415-english-rugby-league-super-league">English Rugby League Super League</a>
        </body>
        </html>
        """
        result = parse_league_catalog(html)
        assert len(result) == 2
        assert result[0]["id"] == 4414
        assert result[0]["slug"] == "english-prem-rugby"
        assert result[0]["name"] == "English Prem Rugby"
        assert result[1]["id"] == 4415
        assert result[1]["slug"] == "english-rugby-league-super-league"
        assert result[1]["name"] == "English Rugby League Super League"

    def test_deduplication_by_id(self):
        """Test that duplicate IDs are deduplicated (first wins)."""
        html = """
        <html>
        <body>
        <a href="/league/4414-english-prem-rugby">English Prem Rugby</a>
        <a href="/season/4414-english-prem-rugby/2025-2026">Different Name</a>
        </body>
        </html>
        """
        result = parse_league_catalog(html)
        assert len(result) == 1
        assert result[0]["id"] == 4414
        assert result[0]["name"] == "English Prem Rugby"

    def test_fallback_to_slug_if_no_name(self):
        """Test fallback to slug when anchor text is empty."""
        html = """
        <html>
        <body>
        <a href="/league/4414-english-prem-rugby"></a>
        </body>
        </html>
        """
        result = parse_league_catalog(html)
        assert len(result) == 1
        assert result[0]["id"] == 4414
        assert result[0]["slug"] == "english-prem-rugby"
        # Empty anchor text -> title-cased slug for a readable display name.
        assert result[0]["name"] == "English Prem Rugby"

    def test_category_none(self):
        """Test that category is None (best-effort)."""
        html = """
        <html>
        <body>
        <a href="/league/4414-english-prem-rugby">English Prem Rugby</a>
        </body>
        </html>
        """
        result = parse_league_catalog(html)
        assert result[0]["category"] is None


class TestLoadSeed:
    def test_load_seed_returns_list(self):
        """Test load_seed returns a list."""
        result = load_seed()
        assert isinstance(result, list)
        assert len(result) >= 50

    def test_load_seed_includes_4414(self):
        """Test load_seed includes the English Prem Rugby (id 4414)."""
        result = load_seed()
        ids = [item["id"] for item in result]
        assert 4414 in ids


class TestMain:
    def test_main_block_assertion(self):
        """Test that the main block self-check passes."""
        html = """
        <html>
        <body>
        <a href="/league/4414-english-prem-rugby">English Prem Rugby</a>
        </body>
        </html>
        """
        result = parse_league_catalog(html)
        assert result[0]["id"] == 4414

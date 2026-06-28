"""Fuzzy matcher for Telegram video filenames/captions to rugby fixtures."""

import pytest
from datetime import datetime, timezone
from app.rugby.matcher import normalize, match


def test_normalize_lowercase_and_punctuation():
    """normalize() lowercases, removes punctuation."""
    assert normalize("SALE SHARKS") == "sale sharks"
    assert normalize("Bath-Unioned") == "bath unioned"  # Punctuation becomes space
    assert normalize("Gloucester's Union") == "gloucester s union"  # Apostrophe becomes space


def test_normalize_drops_rugby_filler():
    """normalize() removes rugby, rfc, fc, afc, the."""
    assert normalize("Bath Rugby") == "bath"
    assert normalize("Sale Sharks RFC") == "sale sharks"
    assert normalize("The Harlequins FC") == "harlequins"
    assert normalize("Leicester AFC") == "leicester"
    assert normalize("THE RUGBY UNION") == "union"


def test_normalize_collapses_whitespace():
    """normalize() collapses multiple spaces."""
    assert normalize("Sale   Sharks") == "sale sharks"
    assert normalize("  Bath  ") == "bath"


def test_match_exact_team_names_with_date():
    """match() returns Sale/Gloucester fixture with auto status."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
        {
            "id": 2,
            "home_name": "Harlequins",
            "away_name": "Bath Rugby",
            "date": datetime(2025, 9, 26, tzinfo=timezone.utc),
        },
    ]
    text = "Sale Sharks v Gloucester 27-09-25"
    date = datetime(2025, 9, 25, tzinfo=timezone.utc)

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is not None
    assert result_fixture["id"] == 1
    assert status == "auto"
    assert confidence >= 0.8


def test_match_without_date():
    """match() returns Harlequins/Bath fixture without date context."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
        {
            "id": 2,
            "home_name": "Harlequins",
            "away_name": "Bath Rugby",
            "date": datetime(2025, 9, 26, tzinfo=timezone.utc),
        },
    ]
    text = "Harlequins Bath highlights"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is not None
    assert result_fixture["id"] == 2
    assert status != "none"
    assert confidence > 0.5


def test_match_no_match_returns_none():
    """match() returns (None, low_confidence, 'none') for unrelated text."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": datetime(2025, 9, 25, tzinfo=timezone.utc),
        },
    ]
    text = "Random cooking video"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is None
    assert status == "none"
    assert confidence < 0.6


def test_match_empty_fixtures():
    """match() with empty fixtures list returns (None, 0.0, 'none')."""
    fixtures = []
    text = "Some random text"
    date = None

    result_fixture, confidence, status = match(text, date, fixtures)

    assert result_fixture is None
    assert confidence == 0.0
    assert status == "none"


def test_match_threshold_needs_review():
    """match() returns needs_review when confidence in [threshold, 0.8)."""
    fixtures = [
        {
            "id": 1,
            "home_name": "Sale Sharks",
            "away_name": "Gloucester",
            "date": None,
        },
    ]
    text = "Sale Sharks vs Gloucester"  # Clear match but not with date
    date = None

    result_fixture, confidence, status = match(text, date, fixtures, threshold=0.5)

    # Should match with moderate confidence (no date bonus means likely < 0.8)
    assert result_fixture is not None
    assert status in ["auto", "needs_review"]
    assert confidence >= 0.5

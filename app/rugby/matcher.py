"""Fuzzy matcher for Telegram video filenames/captions to rugby fixtures.

Normalizes team names and text, scores each fixture based on token containment,
applies optional date-based confidence adjustments.
"""

import re
from datetime import datetime, timezone


# Words to drop during normalization
FILLER_WORDS = {"rugby", "rfc", "fc", "afc", "the"}


def normalize(name: str) -> str:
    """Lowercase, drop punctuation, remove rugby filler words, collapse whitespace.

    Args:
        name: Team name or text to normalize.

    Returns:
        Normalized string.
    """
    # Lowercase
    s = name.lower()
    # Replace punctuation with spaces, keep only alphanumeric and spaces
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    # Remove filler words (whole words only)
    tokens = s.split()
    tokens = [t for t in tokens if t not in FILLER_WORDS]
    # Collapse whitespace
    return " ".join(tokens)


def contains_score(team: str, text: str) -> float:
    """Score how well a team name's tokens appear in normalized text.

    For each significant token (len >= 3) in the team name, check if it
    appears as a substring in the text. Return the fraction found.

    Args:
        team: Normalized team name.
        text: Normalized text to search.

    Returns:
        Fraction of team's significant tokens found in text (0.0 to 1.0).
    """
    tokens = team.split()
    if not tokens:
        return 0.0

    significant = [t for t in tokens if len(t) >= 3]
    if not significant:
        return 0.0

    found = sum(1 for t in significant if t in text)
    return found / len(significant)


def match(
    text: str,
    date: datetime | None,
    fixtures: list[dict],
    threshold: float = 0.6,
) -> tuple[dict | None, float, str]:
    """Fuzzy-match text to the best-scoring fixture.

    Scores each fixture as the average of home and away team containment scores
    in the normalized text. Applies date bonuses/penalties if both text_date and
    fixture_date are present. Returns the highest-scoring fixture if confidence
    >= threshold; status "auto" if >= 0.8, "needs_review" if >= threshold,
    "none" otherwise.

    Args:
        text: Telegram filename/caption text.
        date: Optional match date.
        fixtures: List of fixture dicts (each with home_name, away_name, date, id).
        threshold: Minimum confidence to return a match (default 0.6).

    Returns:
        Tuple of (best_fixture or None, confidence float, status string).
        status in {"auto", "needs_review", "none"}.
    """
    if not fixtures:
        return (None, 0.0, "none")

    normalized_text = normalize(text)
    best_fixture = None
    best_confidence = 0.0

    for fixture in fixtures:
        # Score home and away team containment
        home_score = contains_score(normalize(fixture["home_name"]), normalized_text)
        away_score = contains_score(normalize(fixture["away_name"]), normalized_text)
        confidence = (home_score + away_score) / 2.0

        # Apply date adjustments
        if date is not None and fixture.get("date") is not None:
            fixture_date = fixture["date"]
            # Normalize to UTC if needed
            if fixture_date.tzinfo is None:
                fixture_date = fixture_date.replace(tzinfo=timezone.utc)
            if date.tzinfo is None:
                date_to_check = date.replace(tzinfo=timezone.utc)
            else:
                date_to_check = date

            days_diff = abs((fixture_date.date() - date_to_check.date()).days)

            if days_diff <= 3:
                # Date match: bonus
                confidence = min(1.0, confidence + 0.15)
            elif days_diff > 10:
                # Large date mismatch: penalty
                confidence *= 0.7

        if confidence > best_confidence:
            best_confidence = confidence
            best_fixture = fixture

    # Determine status
    if best_confidence >= threshold:
        if best_confidence >= 0.8:
            status = "auto"
        else:
            status = "needs_review"
        return (best_fixture, best_confidence, status)
    else:
        return (None, best_confidence, "none")

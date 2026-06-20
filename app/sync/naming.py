"""Smart naming: season/episode detection and path rendering."""

import re


def detect_season_episode(text: str | None) -> tuple[int, int]:
    """
    Detect season and episode numbers from text using ordered regex patterns.

    Tries patterns in order:
    1. S##E## (case-insensitive)
    2. ##x## (case-insensitive)
    3. Season N Episode N (case-insensitive, DOTALL)
    4. Fallback to (1, 1)

    Args:
        text: String to parse, or None.

    Returns:
        Tuple of (season, episode) integers.
    """
    if not text:
        return (1, 1)

    # Pattern 1: S01E02
    match = re.search(r"S(\d+)E(\d+)", text, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Pattern 2: 1x02
    match = re.search(r"(\d+)x(\d+)", text, re.IGNORECASE)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Pattern 3: Season N Episode N
    match = re.search(r"Season\s+(\d+).*Episode\s+(\d+)", text, re.IGNORECASE | re.DOTALL)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Fallback
    return (1, 1)


def render_path(template: str, tokens: dict[str, str | int]) -> str:
    """
    Render a path template with token substitution.

    Supports Python format specifiers (e.g., {season:02d}).
    Falls back to {original} if KeyError (missing token).

    Args:
        template: Path template string (e.g., "{channel}/{topic}/{title}{ext}").
        tokens: Dictionary of token names to values.

    Returns:
        Rendered path string.

    Raises:
        ValueError: If template contains missing tokens and no {original} fallback.
    """
    try:
        return template.format(**tokens)
    except KeyError:
        # Fallback to {original}
        if "original" in tokens:
            return tokens["original"]
        raise ValueError(f"Template contains missing tokens and no fallback: {template}")

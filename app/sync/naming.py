"""Smart naming: season/episode detection and path rendering."""

import re

# Matches the formats detect_season_episode understands (for a yes/no check).
_SE_PATTERN = re.compile(
    r"(S\d+E\d+|\d+x\d+|Season\s+\d+.*Episode\s+\d+)", re.IGNORECASE
)


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


def choose_target_path(item, sub, extra: dict | None = None):
    """Decide the relative download path for an item.

    Uses ``sub.rename_template`` when an S/E pattern is detected (and
    season_detection is on) **or** a plugin supplied ``extra`` tokens (e.g.
    rugby league/teams); otherwise keeps the original filename. Plugin tokens
    let a template apply even without an S##E## marker.

    Returns ``(relative_path, season|None, episode|None, used_template)``.
    """
    extra = extra or {}
    text = (item.file_name or item.caption or "") if item else ""
    has_pattern = bool(_SE_PATTERN.search(text))
    has_template = bool(sub and getattr(sub, "rename_template", None))
    use_template = has_template and (
        (getattr(sub, "season_detection", False) and has_pattern) or bool(extra)
    )

    if not use_template:
        fallback = (item.file_name if item and item.file_name
                    else f"{getattr(item, 'tg_msg_id', 'media')}.mp4")
        return fallback, None, None, False

    season, episode = detect_season_episode(text) if has_pattern else (None, None)
    title = item.file_name.rsplit(".", 1)[0] if item and item.file_name else "unknown"
    ext = "." + item.file_name.rsplit(".", 1)[-1] if item and item.file_name else ""
    tokens = {
        "channel": (sub.channel.title if getattr(sub, "channel", None) else "Unknown"),
        "topic": (sub.topic.title if getattr(sub, "topic", None) else "General"),
        "season": season if season is not None else 1,
        "episode": episode if episode is not None else 1,
        "title": title,
        "ext": ext,
        "original": item.file_name or "unknown" if item else "unknown",
        "date": item.date_posted.isoformat() if item and item.date_posted else "",
        **extra,
    }
    return render_path(sub.rename_template, tokens), season, episode, True

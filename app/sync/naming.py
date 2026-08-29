"""Smart naming: season/episode detection and path rendering."""

import re

# Chars illegal on common filesystems (Windows/SMB shares included); collapsed
# so a channel/league title is safe as a single path segment.
_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


def safe_segment(name: str, default: str = "Downloads") -> str:
    """Sanitize a string into one filesystem-safe path segment."""
    cleaned = _UNSAFE.sub(" ", (name or "")).strip(" .")
    return cleaned or default

# Matches the formats detect_season_episode understands (for a yes/no check).
_SE_PATTERN = re.compile(
    r"(S\d+E\d+|\d+x\d+|Season\s+\d+.*Episode\s+\d+)", re.IGNORECASE
)

# Template tokens that are only meaningful once an S##E## pattern was detected.
# A template without them (e.g. "{topic}/{title}.{ext}") needs no detection.
_SE_TOKENS = re.compile(r"\{(season|episode)\b")


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
        rendered = template.format(**tokens)
    except KeyError:
        # Fallback to {original}
        if "original" in tokens:
            return tokens["original"]
        raise ValueError(f"Template contains missing tokens and no fallback: {template}")
    # Collapse accidental doubled dots in the filename (e.g. a "{title}.{ext}"
    # template where {ext} already carries the leading dot -> "name..mp4").
    # Only the last path segment, so directory names are untouched.
    head, sep, tail = rendered.rpartition("/")
    return head + sep + re.sub(r"\.{2,}", ".", tail)


def choose_target_path(item, sub, extra: dict | None = None):
    """Decide the relative download path for an item.

    Uses ``sub.rename_template`` whenever it can be rendered: templates that
    reference {season}/{episode} need a detected S##E## pattern (with
    season_detection on) or plugin ``extra`` tokens; every other template
    (e.g. "{topic}/{title}.{ext}") applies unconditionally. Only a
    subscription with no template at all keeps the original filename.

    Returns ``(relative_path, season|None, episode|None, used_template)``.
    """
    extra = extra or {}
    text = (item.file_name or item.caption or "") if item else ""
    has_pattern = bool(_SE_PATTERN.search(text))
    template = (getattr(sub, "rename_template", None) or "") if sub else ""
    needs_pattern = bool(_SE_TOKENS.search(template))
    use_template = bool(template) and (
        bool(extra)
        or not needs_pattern
        or (getattr(sub, "season_detection", False) and has_pattern)
    )

    if not use_template:
        fallback = (item.file_name if item and item.file_name
                    else f"{getattr(item, 'tg_msg_id', 'media')}.mp4")
        # Always nest under a subfolder so nothing lands loose in the storage
        # root. The source topic names the competition, so it wins over the
        # channel title; then sub name, else default.
        folder = (getattr(getattr(sub, "topic", None), "title", None)
                  or getattr(getattr(sub, "channel", None), "title", None)
                  or getattr(sub, "name", None)) if sub else None
        return f"{safe_segment(folder)}/{fallback}", None, None, False

    detect = has_pattern and getattr(sub, "season_detection", False)
    season, episode = detect_season_episode(text) if detect else (None, None)
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

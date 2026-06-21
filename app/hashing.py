"""Quick content fingerprint for media dedup / renamed-file detection.

Hashes file size + first 1MB + last 1MB instead of the whole file — near-instant
even on multi-GB videos, and collision-safe for real media. Used to recognise a
file that was renamed/moved (so we don't re-download it) and to skip storing a
duplicate that another subscription already fetched.
"""
import hashlib
from pathlib import Path

_CHUNK = 1024 * 1024  # 1 MB


def quick_hash(path: str | Path) -> str | None:
    """sha256 of (size | head 1MB | tail 1MB). None if the file is unreadable."""
    try:
        p = Path(path)
        size = p.stat().st_size
        h = hashlib.sha256()
        h.update(str(size).encode())
        with open(p, "rb") as f:
            h.update(f.read(_CHUNK))
            if size > _CHUNK:
                # Seek to the last chunk (overlaps head for files < 2MB — harmless).
                f.seek(max(0, size - _CHUNK))
                h.update(f.read(_CHUNK))
        return h.hexdigest()
    except OSError:
        return None

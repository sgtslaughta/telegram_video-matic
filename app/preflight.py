"""Startup preflight: validate required env + data-dir writability and fail
with a clear, single-line message instead of a stack trace.

Runs in `app/__main__.py` BEFORE the app is imported, so a missing secret
(pydantic ValidationError at import) or an unwritable SQLite dir
(OperationalError deep in SQLAlchemy) never reach the user as a traceback.
"""
import os

from app.utils.log import log

# Vars the app cannot start without. Extend as new hard requirements appear.
REQUIRED_ENV = ("TVM_SECRET_KEY",)


def _fail(msg: str) -> None:
    """Log an actionable error and exit non-zero with no traceback."""
    log(msg, "ERROR")
    raise SystemExit(1)


def _sqlite_dir(database_url: str) -> str | None:
    """Return the directory that must hold the SQLite file, or None for
    non-file DBs (postgres/mysql/:memory:) where there's nothing local to check."""
    from sqlalchemy.engine import make_url

    url = make_url(database_url)
    if "sqlite" not in url.drivername:
        return None
    db = url.database  # absolute/relative file path, ":memory:", or None
    if not db or db == ":memory:":
        return None
    return os.path.dirname(db) or "."


def check() -> None:
    """Validate startup prerequisites. Exits the process on the first failure."""
    for name in REQUIRED_ENV:
        val = os.getenv(name)
        if not val or not val.strip():
            hint = ""
            if name == "TVM_SECRET_KEY":
                hint = (" Generate one with: "
                        "python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
            _fail(f"Required environment variable {name} is missing or empty.{hint}")

    data_dir = _sqlite_dir(os.getenv("DATABASE_URL", "sqlite+aiosqlite:////data/tvm.sqlite"))
    if data_dir is None:
        return

    try:
        os.makedirs(data_dir, exist_ok=True)
        probe = os.path.join(data_dir, ".tvm-write-test")
        with open(probe, "w") as f:
            f.write("ok")
        os.remove(probe)
    except OSError as e:
        _fail(
            f"Database directory {data_dir!r} is not writable "
            f"(process uid={os.getuid()} gid={os.getgid()}): {e}. "
            "On Unraid/Docker the bind-mounted appdata dir must be writable by "
            "this user — set PUID/PGID to the dir's owner, or chown the host dir."
        )

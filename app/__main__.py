"""Container entrypoint: `python -m app`.

Runs preflight checks (clear errors, no traceback) before importing the app,
then launches uvicorn.
"""
import os

from app.preflight import check


def main() -> None:
    check()
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),  # noqa: S104  # nosec B104 — container binds all ifaces
        port=int(os.getenv("PORT", "8000")),
    )


if __name__ == "__main__":
    main()

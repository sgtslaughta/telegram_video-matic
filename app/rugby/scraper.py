import json
import re
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup


class RugbyScrapeError(Exception):
    """Raised when scraping fails."""

    pass


def parse_league_catalog(html: str) -> list[dict]:
    """
    Parse the thesportsdb /sport/rugby page.
    Return list of {"id": int, "slug": str, "name": str, "category": str | None}.
    """
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r"^/(?:season|league)/(\d+)-([a-z0-9\-]+)")

    seen_ids = {}
    for anchor in soup.find_all("a"):
        href = anchor.get("href")
        if not href:
            continue

        match = pattern.match(href)
        if not match:
            continue

        league_id = int(match.group(1))
        slug = match.group(2)

        # Skip if already seen (first wins)
        if league_id in seen_ids:
            continue

        name = anchor.get_text(strip=True) or slug
        entry = {
            "id": league_id,
            "slug": slug,
            "name": name,
            "category": None,
        }
        seen_ids[league_id] = entry

    return list(seen_ids.values())


def load_seed() -> list[dict]:
    """
    Read app/rugby/seed_leagues.json (resolve path relative to THIS file).
    Return the list.
    """
    current_dir = Path(__file__).parent
    seed_path = current_dir / "seed_leagues.json"
    with open(seed_path) as f:
        return json.load(f)


async def fetch_league_catalog(
    client: Optional[httpx.AsyncClient] = None, timeout: float = 15.0
) -> list[dict]:
    """
    GET https://www.thesportsdb.com/sport/rugby, then parse_league_catalog(resp.text).
    On ANY failure raise RugbyScrapeError. Explicit timeout= on the request (bandit).
    """
    should_close = False
    if client is None:
        client = httpx.AsyncClient()
        should_close = True

    try:
        response = await client.get(
            "https://www.thesportsdb.com/sport/rugby", timeout=timeout
        )
        response.raise_for_status()
        return parse_league_catalog(response.text)
    except Exception as e:
        raise RugbyScrapeError(f"Failed to fetch league catalog: {e}") from e
    finally:
        if should_close:
            await client.aclose()


async def download_logo(
    url: str, dest: str, client: Optional[httpx.AsyncClient] = None, timeout: float = 15.0
) -> None:
    """
    GET url, write bytes to dest (create parent dirs).
    Raise RugbyScrapeError on failure.
    """
    should_close = False
    if client is None:
        client = httpx.AsyncClient()
        should_close = True

    try:
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        response = await client.get(url, timeout=timeout)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        raise RugbyScrapeError(f"Failed to download logo from {url}: {e}") from e
    finally:
        if should_close:
            await client.aclose()


if __name__ == "__main__":
    html = """
    <html>
    <body>
    <a href="/league/4414-english-prem-rugby">English Prem Rugby</a>
    </body>
    </html>
    """
    result = parse_league_catalog(html)
    assert result[0]["id"] == 4414, f"Expected id 4414, got {result[0]['id']}"
    print("Self-check passed: parse_league_catalog returns correct id")

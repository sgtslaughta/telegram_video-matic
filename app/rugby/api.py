import asyncio
import time
import httpx


class RugbyApiError(Exception):
    """Exception for rugby API errors."""

    def __init__(self, endpoint: str, detail: str):
        self.endpoint = endpoint
        self.detail = detail
        super().__init__(f"{endpoint}: {detail}")


class RugbyApi:
    """Async client for thesportsdb's free v1 JSON API."""

    def __init__(
        self,
        api_key: str = "123",
        base: str = "https://www.thesportsdb.com/api/v1/json",
        timeout: float = 15.0,
        min_interval: float = 0.0,
        max_interval: float = 30.0,
        client: "httpx.AsyncClient | None" = None,
    ):
        self.api_key = api_key
        self.base = base
        self.timeout = timeout
        self.min_interval = min_interval
        # Adaptive throttle: starts at min_interval, climbs on 429 (×1.5, capped
        # at max_interval), decays back toward min on sustained success. One
        # client = one moving spacing, so the whole scan self-tunes to the limit.
        self.max_interval = max(max_interval, min_interval)
        self._interval = min_interval
        self.client = client
        self._last_request_time = 0.0

    async def fetch_season(self, league_id: int, season: str) -> list[dict]:
        """Fetch events for a league and season."""
        endpoint = "eventsseason.php"
        url = f"{self.base}/{self.api_key}/{endpoint}"
        params = {"id": league_id, "s": season}

        try:
            data = await self._get(url, params, endpoint)
            events = data.get("events")
            return events if events is not None else []
        except RugbyApiError:
            raise

    async def fetch_round(self, league_id: int, rnd: int, season: str) -> list[dict]:
        """Fetch one round of a season. Free tier serves these uncapped, unlike
        eventsseason (which truncates to 15), so round-by-round gives full
        coverage."""
        endpoint = "eventsround.php"
        url = f"{self.base}/{self.api_key}/{endpoint}"
        data = await self._get(url, {"id": league_id, "r": rnd, "s": season}, endpoint)
        return data.get("events") or []

    async def fetch_past_league(self, league_id: int) -> list[dict]:
        """Most-recent ~15 played events for a league (catches finals/playoffs
        whose round numbering the per-round scan would miss)."""
        endpoint = "eventspastleague.php"
        url = f"{self.base}/{self.api_key}/{endpoint}"
        data = await self._get(url, {"id": league_id}, endpoint)
        return data.get("events") or []

    async def lookup_team(self, team_id: int) -> dict | None:
        """Lookup a team by ID."""
        endpoint = "lookupteam.php"
        url = f"{self.base}/{self.api_key}/{endpoint}"
        params = {"id": team_id}

        try:
            data = await self._get(url, params, endpoint)
            teams = data.get("teams")
            if teams is None or len(teams) == 0:
                return None
            return teams[0]
        except RugbyApiError:
            raise

    async def list_seasons(self, league_id: int) -> list[str]:
        """List all seasons for a league."""
        endpoint = "search_all_seasons.php"
        url = f"{self.base}/{self.api_key}/{endpoint}"
        params = {"id": league_id}

        try:
            data = await self._get(url, params, endpoint)
            seasons = data.get("seasons")
            if seasons is None:
                return []
            return [s["strSeason"] for s in seasons]
        except RugbyApiError:
            raise

    async def _get(
        self, url: str, params: dict, endpoint: str
    ) -> dict:
        """Internal GET with adaptive throttling + error handling."""
        # Space requests by the current adaptive interval.
        if self._interval > 0:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self._interval:
                await asyncio.sleep(self._interval - elapsed)
        self._last_request_time = time.monotonic()

        if self.client is not None:
            return await self._fetch_with_client(
                self.client, url, params, endpoint
            )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._fetch_with_client(client, url, params, endpoint)

    def _on_429(self, response) -> float:
        """Widen the adaptive interval and return how long to wait now."""
        self._interval = min(max(self._interval, 1.0) * 1.5, self.max_interval)
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), self.max_interval)
            except ValueError:
                pass
        return self._interval

    def _on_success(self):
        """Decay the interval back toward the configured floor."""
        self._interval = max(self.min_interval, self._interval * 0.85)

    async def _fetch_with_client(
        self, client: httpx.AsyncClient, url: str, params: dict, endpoint: str
    ) -> dict:
        """Fetch with adaptive 429 backoff (honors Retry-After)."""
        try:
            for _ in range(5):
                response = await client.get(url, params=params, timeout=self.timeout)
                if response.status_code == 429:
                    await asyncio.sleep(self._on_429(response))
                    continue
                break

            if response.status_code == 429:
                raise RugbyApiError(endpoint, "HTTP 429: rate limited after retries")
            if response.status_code >= 400:
                raise RugbyApiError(
                    endpoint, f"HTTP {response.status_code}: {response.text}")

            self._on_success()
            return response.json()
        except httpx.RequestError as e:
            raise RugbyApiError(endpoint, f"Connection error: {str(e)}")
        except ValueError as e:
            raise RugbyApiError(endpoint, f"Invalid JSON: {str(e)}")

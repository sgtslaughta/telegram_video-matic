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
        client: "httpx.AsyncClient | None" = None,
    ):
        self.api_key = api_key
        self.base = base
        self.timeout = timeout
        self.min_interval = min_interval
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
        """Internal GET request with rate limiting and error handling."""
        # ponytail: simple throttle
        if self.min_interval > 0:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

        self._last_request_time = time.monotonic()

        if self.client is not None:
            return await self._fetch_with_client(
                self.client, url, params, endpoint
            )
        else:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                return await self._fetch_with_client(
                    client, url, params, endpoint
                )

    async def _fetch_with_client(
        self, client: httpx.AsyncClient, url: str, params: dict, endpoint: str
    ) -> dict:
        """Fetch using a provided client."""
        try:
            response = await client.get(
                url, params=params, timeout=self.timeout
            )

            if response.status_code >= 400:
                raise RugbyApiError(
                    endpoint,
                    f"HTTP {response.status_code}: {response.text}",
                )

            data = response.json()
            return data
        except httpx.RequestError as e:
            raise RugbyApiError(endpoint, f"Connection error: {str(e)}")
        except ValueError as e:
            raise RugbyApiError(endpoint, f"Invalid JSON: {str(e)}")

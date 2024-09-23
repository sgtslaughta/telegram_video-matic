import requests


class SportsDBClient:
    BASE_URL_V1 = "https://www.thesportsdb.com/api/v1/json"
    BASE_URL_V2 = "https://www.thesportsdb.com/api/v2/json"

    def __init__(self, api_key=None, version="v1"):
        """
        Initialize the client.
        :param api_key: Optional API key for premium or v2 access
        :param version: 'v1' or 'v2', to select the API version
        """
        self.api_key = api_key if api_key else "3"  # Free tier default key is "3"
        self.version = version
        self.base_url = self.BASE_URL_V1 if version == "v1" else self.BASE_URL_V2

    def _get(self, endpoint, params=None):
        try:
            for _ in params:
                params[_] = params[_].replace(" ", "_")
            # For v1: include the API key in the URL, for v2: use it in headers
            if self.version == "v1":
                url = f"{self.base_url}/{self.api_key}/{endpoint}"
                response = requests.get(url, params=params)
            else:
                url = f"{self.base_url}/{endpoint}"
                headers = {'X-API-KEY': self.api_key}
                response = requests.get(url, params=params, headers=headers)

            # Raise an error for bad status codes
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    # --- SEARCH METHODS ---

    def search_team_by_name(self, team_name):
        params = {'t': team_name}
        return self._get("searchteams.php", params)

    def search_team_by_shortcode(self, shortcode):
        params = {'sname': shortcode}
        return self._get("searchteams.php", params)

    def search_player_by_name_or_team(self, player_name=None, team=None):
        if team and player_name:
            raise ValueError("Either player_name or team should be provided, not both.")
        if team:
            params = {'t': team}
        else:
            params = {'p': player_name}
        return self._get("searchplayers.php", params)

    def search_event_by_name(self, event_name, season=None):
        params = {'e': event_name}
        if season:
            params['s'] = season
        return self._get("searchevents.php", params)

    def search_filename(self, event_file_name):
        params = {'e': event_file_name}
        return self._get("searchfilename.php", params)

    def search_venue(self, venue_name):
        params = {'t': venue_name}
        return self._get("searchvenues.php", params)

    # --- LISTING METHODS ---

    def list_all_sports(self):
        return self._get("all_sports.php")

    def list_all_leagues(self):
        return self._get("all_leagues.php")

    def list_all_countries(self):
        return self._get("all_countries.php")

    def list_leagues_by_country(self, country, sport=None):
        params = {'c': country}
        if sport:
            params['s'] = sport
        return self._get("search_all_leagues.php", params)

    def list_all_seasons_in_league(self, league_id):
        params = {'id': league_id}
        return self._get("search_all_seasons.php", params)

    def list_teams_in_league(self, league_name, sport=None, country=None):
        params = {'l': league_name}
        if sport:
            params['s'] = sport
        if country:
            params['c'] = country
        return self._get("search_all_teams.php", params)

    # --- LOOKUP METHODS ---

    def lookup_league_by_id(self, league_id):
        params = {'id': league_id}
        return self._get("lookupleague.php", params)

    def lookup_team_by_id(self, team_id):
        params = {'id': team_id}
        return self._get("lookupteam.php", params)

    def lookup_player_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookupplayer.php", params)

    def lookup_players_by_team(self, team_id):
        params = {'id': team_id}
        return self._get("lookup_all_players.php", params)

    def lookup_venue_by_id(self, venue_id):
        params = {'id': venue_id}
        return self._get("lookupvenue.php", params)

    def lookup_event_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookupevent.php", params)

    def lookup_event_stats_by_id(self, event_id):
        return self._get(f"lookupeventstats.php?id={event_id}")

    def lookup_event_lineup_by_id(self, event_id):
        return self._get(f"lookuplineup.php?id={event_id}")

    def lookup_event_timeline_by_id(self, event_id):
        return self._get(f"lookuptimeline.php?id={event_id}")

    def lookup_player_honors_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookuphonours.php", params)

    def lookup_player_milestones_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookupmilestones.php", params)

    def lookup_player_former_teams_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookupformerteams.php", params)

    def lookup_player_contracts_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookupcontracts.php", params)

    # --- SCHEDULE METHODS ---

    def get_next_events_by_team(self, team_id):
        params = {'id': team_id}
        return self._get("eventsnext.php", params)

    def get_next_events_by_league(self, league_id):
        params = {'id': league_id}
        return self._get("eventsnextleague.php", params)

    def get_last_events_by_team(self, team_id):
        params = {'id': team_id}
        return self._get("eventslast.php", params)

    def get_last_events_by_league(self, league_id):
        params = {'id': league_id}
        return self._get("eventspastleague.php", params)

    def get_events_on_specific_day(self, date, sport=None, league=None):
        params = {'d': date}
        if sport:
            params['s'] = sport
        if league:
            params['l'] = league
        return self._get("eventsday.php", params)

    def get_tv_events_on_day(self, date, sport=None, country=None):
        params = {'d': date}
        if sport:
            params['s'] = sport
        if country:
            params['a'] = country
        return self._get("eventstv.php", params)

    def get_league_events_by_season(self, league_id, season):
        params = {'id': league_id, 's': season}
        return self._get("eventsseason.php", params)

    # --- VIDEO HIGHLIGHTS (Premium) ---

    def get_event_highlights(self, date=None, league=None):
        params = {}
        if date:
            params['d'] = date
        if league:
            params['l'] = league
        return self._get("eventshighlights.php", params)

    # --- LIVE SCORES (Premium) ---

    def get_livescore(self, sport=None, league_id=None):
        if sport:
            return self._get(f"livescore/{sport}")
        elif league_id:
            return self._get(f"livescore/{league_id}")
        else:
            return self._get(f"livescore/all")


class SportsDBv2:
    BASE_URL = "https://www.thesportsdb.com/api/v2/json"
    def __init__(self, api_key):
        self.api_key = api_key

    def _get(self, endpoint, params=None):
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            headers = {'X-API-KEY': self.api_key}
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    # Search methods
    def search_league(self, league_name):
        league_name = league_name.replace(" ", "_")
        params = {'league': league_name}
        return self._get("search/league/", params)

    def search_team(self, team_name):
        team_name = team_name.replace(" ", "_")
        params = {'team': team_name}
        return self._get("search/team/", params)

    def search_player(self, player_name):
        player_name = player_name.replace(" ", "_")
        params = {'player': player_name}
        return self._get("search/player/", params)

    def search_venue(self, venue_name):
        venue_name = venue_name.replace(" ", "_")
        params = {'venue': venue_name}
        return self._get("search/venue/", params)

    def search_event(self, event_name):
        event_name = event_name.replace(" ", "_")
        params = {'event': event_name}
        return self._get("search/event", params)

    def search_alternate_league(self, league_name):
        league_name = league_name.replace(" ", "_")
        params = {'league': league_name}
        return self._get("searchalternate/league/", params)

    def get_livescore(self, sport=None, league_id=None, team_id=None):
        if sport:
            return self._get(f"livescore/{sport}")
        elif league_id:
            return self._get(f"livescore/{league_id}")
        elif team_id:
            return self._get(f"livescore/{team_id}")
        else:
            return self._get(f"livescore/all")

    # Lookup methods
    def lookup_league(self, league_id):
        return self._get(f"lookup/league/{league_id}")

    def lookup_team(self, team_id):
        return self._get(f"lookup/team/{team_id}")

    def lookup_team_equipment(self, team_id):
        return self._get(f"lookup/team_equipment/{team_id}")

    def lookup_player(self, player_id):
        return self._get(f"lookup/player/{player_id}")

    def lookup_player_contracts(self, player_id):
        return self._get(f"lookup/player_contracts/{player_id}")

    def lookup_player_honours(self, player_id):
        return self._get(f"lookup/player_honours/{player_id}")

    def lookup_player_milestones(self, player_id):
        return self._get(f"lookup/player_milestones/{player_id}")

    def lookup_player_teams(self, player_id):
        return self._get(f"lookup/player_teams/{player_id}")

    def lookup_event(self, event_id):
        return self._get(f"lookup/event/{event_id}")

    def lookup_event_lineup(self, event_id):
        return self._get(f"lookup/event_lineup/{event_id}")

    def lookup_event_results(self, event_id):
        return self._get(f"lookup/event_results/{event_id}")

    def lookup_event_stats(self, event_id):
        return self._get(f"lookup/event_stats/{event_id}")

    def lookup_event_timeline(self, event_id):
        return self._get(f"lookup/event_timeline/{event_id}")

    def lookup_event_tv(self, event_id):
        return self._get(f"lookup/event_tv/{event_id}")

    def lookup_event_highlights(self, event_id):
        return self._get(f"lookup/event_highlights/{event_id}")

    def lookup_venue(self, venue_id):
        return self._get(f"lookup/venue/{venue_id}")

    # List 'ALL' methods
    def list_all_countries(self):
        return self._get("all/countries")

    def list_all_sports(self):
        return self._get("all/sports")

    def list_all_leagues(self):
        return self._get("all/leagues")

    # List 'lookup' methods
    def list_seasons(self, league_id):
        return self._get(f"list/seasons/{league_id}")

    def list_season_posters(self, league_id):
        return self._get(f"list/seasonposters/{league_id}")

    def list_players(self, team_id=None, team_name=None, league_id=None):
        if team_id:
            return self._get(f"list/players/{team_id}")
        elif team_name:
            team_name = team_name.replace(" ", "_")
            return self._get(f"list/players/{team_name}")
        elif league_id:
            return self._get(f"list/players/{league_id}")

    def list_teams(self, league_id=None, league_name=None):
        if league_id:
            return self._get(f"list/teams/{league_id}")
        elif league_name:
            league_name = league_name.replace(" ", "_")
            return self._get(f"list/teams/{league_name}")

    # Filter methods
    def filter_events(self, league_id, season):
        return self._get(f"filter/events/{league_id}/{season}")

    def filter_events_by_day(self, date):
        return self._get(f"filter/events/day/{date}")

    def filter_tv_events_by_day(self, date):
        return self._get(f"filter/tv/day/{date}")

    def filter_tv_events_by_channel(self, channel):
        channel = channel.replace(" ", "_")
        return self._get(f"filter/tv/channel/{channel}")

    def filter_tv_events_by_country(self, country):
        country = country.replace(" ", "_")
        return self._get(f"filter/tv/country/{country}")

    def filter_tv_events_by_sport(self, sport):
        sport = sport.replace(" ", "_")
        return self._get(f"filter/tv/sport/{sport}")

    # Schedule methods
    def schedule_next_games_by_league(self, league_id):
        return self._get(f"schedule/next/league/{league_id}")

    def schedule_previous_games_by_league(self, league_id):
        return self._get(f"schedule/previous/league/{league_id}")

    def schedule_next_games_by_team(self, team_id):
        return self._get(f"schedule/next/team/{team_id}")

    def schedule_previous_games_by_team(self, team_id):
        return self._get(f"schedule/previous/team/{team_id}")

    def schedule_games_by_league_and_season(self, league_id, season):
        return self._get(f"schedule/league/{league_id}/{season}")


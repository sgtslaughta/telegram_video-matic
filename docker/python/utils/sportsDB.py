import requests


class SportsDBClient:
    BASE_URL_V1 = "https://www.thesportsdb.com/api/v1/json/3"
    BASE_URL_V2 = "https://www.thesportsdb.com/api/v2/json"

    def __init__(self, api_key=None):
        self.api_key = api_key

    def _get(self, endpoint, params=None):
        try:
            url = f"{self.BASE_URL_V1}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None

    def _get_premium(self, endpoint, params=None):
        if not self.api_key:
            print("Premium API key required for this operation.")
            return None
        try:
            url = f"{self.BASE_URL_V2}/{endpoint}"
            headers = {'X-API-KEY': self.api_key}
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error fetching premium data: {e}")
            return None

    # Basic API Endpoints
    def search_team_by_name(self, team_name):
        params = {'t': team_name}
        return self._get("searchteams.php", params)

    def search_team_by_shortcode(self, short_code):
        params = {'sname': short_code}
        return self._get("searchteams.php", params)

    def search_player_by_name(self, player_name):
        params = {'p': player_name}
        return self._get("searchplayers.php", params)

    def search_event_by_name(self, event_name, season=None):
        params = {'e': event_name}
        if season:
            params['s'] = season
        return self._get("searchevents.php", params)

    def search_event_by_filename(self, filename):
        params = {'e': filename}
        return self._get("searchfilename.php", params)

    def search_venue_by_name(self, venue_name):
        params = {'t': venue_name}
        return self._get("searchvenues.php", params)

    def list_all_sports(self):
        return self._get("all_sports.php")

    def list_all_leagues(self):
        return self._get("all_leagues.php")

    def list_all_countries(self):
        return self._get("all_countries.php")

    def list_leagues_by_country(self, country_name, sport=None):
        params = {'c': country_name}
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

    def lookup_league_by_id(self, league_id):
        params = {'id': league_id}
        return self._get("lookupleague.php", params)

    def lookup_team_by_id(self, team_id):
        params = {'id': team_id}
        return self._get("lookupteam.php", params)

    def lookup_player_by_id(self, player_id):
        params = {'id': player_id}
        return self._get("lookupplayer.php", params)

    def lookup_venue_by_id(self, venue_id):
        params = {'id': venue_id}
        return self._get("lookupvenue.php", params)

    def lookup_event_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookupevent.php", params)

    def lookup_event_stats_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookupeventstats.php", params)

    def lookup_event_lineup_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookuplineup.php", params)

    def lookup_timeline_by_event_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookuptimeline.php", params)

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

    def lookup_event_player_results_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("eventresults.php", params)

    def lookup_event_tv_by_id(self, event_id):
        params = {'id': event_id}
        return self._get("lookuptv.php", params)

    def lookup_league_table_by_league_and_season(self, league_id, season):
        params = {'l': league_id, 's': season}
        return self._get("lookuptable.php", params)

    def lookup_team_equipment_by_id(self, team_id):
        params = {'id': team_id}
        return self._get("lookupequipment.php", params)

    def list_loved_teams_and_players(self, username):
        params = {'u': username}
        return self._get("searchloves.php", params)

    # Premium (Patreon) API Endpoints
    def get_next_5_events_by_team(self, team_id):
        params = {'id': team_id}
        return self._get_premium(f"eventsnext.php", params)

    def get_next_15_events_by_league(self, league_id):
        params = {'id': league_id}
        return self._get_premium(f"eventsnextleague.php", params)

    def get_last_5_events_by_team(self, team_id):
        params = {'id': team_id}
        return self._get_premium(f"eventslast.php", params)

    def get_last_15_events_by_league(self, league_id):
        params = {'id': league_id}
        return self._get_premium(f"eventspastleague.php", params)

    def get_events_in_round(self, league_id, round_num, season):
        params = {'id': league_id, 'r': round_num, 's': season}
        return self._get_premium(f"eventsround.php", params)

    def get_events_on_day(self, date, league_id=None, sport=None):
        params = {'d': date}
        if league_id:
            params['l'] = league_id
        if sport:
            params['s'] = sport
        return self._get_premium(f"eventsday.php", params)

    def get_tv_events_on_day(self, date, sport=None, country=None):
        params = {'d': date}
        if sport:
            params['s'] = sport
        if country:
            params['c'] = country
        return self._get_premium(f"eventstv.php", params)

    def get_event_highlights(self, date=None, league=None):
        params = {}
        if date:
            params['d'] = date
        if league:
            params['l'] = league
        return self._get_premium(f"eventshighlights.php", params)

    def get_livescore(self, sport):
        return self._get_premium(f"livescore/{sport}")

    def get_schedule_next_events_by_league(self, league_id):
        return self._get_premium(f"schedule/next/league/{league_id}")

    def get_schedule_previous_events_by_team(self, team_id):
        return self._get_premium(f"schedule/previous/team/{team_id}")

    def get_events_in_league_by_season(self, league_id, season):
        return self._get(f"eventsseason.php", {'id': league_id, 's': season})

    # Add additional V2 premium endpoints as needed

# # Example usage:
# client = SportsDBClient(api_key="your_api_key")
# response = client.search_team_by_name("Arsenal")
# if response:
#     print(response.json())

import asyncio

import pandas as pd
import streamlit as st

from .data_utils import TGAccount, pull_topics
from .db_utils import DBHelper, Topic
from .monitor_utils import is_monitored, add_monitored, remove_monitored
from .sportsDB import SportsDBClient

TOPIC_NAMES = {
    'Gallagher Premiership': 'English Premiership Rugby',
    'URC': 'United Rugby Championship',
    '6 Nations': 'Six Nations Championship',
    'Top 14': 'French Top 14',
    '2019 World Cup': 'Rugby World Cup',
    'World Cup': 'Rugby World Cup',
    'Super Rugby Americas': 'Super Liga Americana',
    'The Rugby Championship': 'Rugby Championship',
    'Pro D2': 'French Pro D2',
    'Summer/Autumn Nations': 'Autumn Nations Cup',
    'NPC/Farah Palmer Cup': 'New Zealand National Provincial Championship',
    'URBA': 'URBA Top 12',
    'U20s': 'Six Nations Under 20s Championship'
}
LEAGUE_IDS = {
    'English Premiership Rugby': '4414',
    'United Rugby Championship': '4446',
    'Six Nations Championship': '4714',
    'French Top 14': '4430',
    'Rugby World Cup': '4574',
    'Super Liga Americana': '4374',
    'Rugby Championship': '4986',
    'French Pro D2': '5172',
    'Autumn Nations Cup': '4375',
    'New Zealand National Provincial Championship': '5278',
    'URBA Top 12': '5165',
    'URBA': '5165',
}
TEAM_IDS = {
    'Ireland Rugby': '137130',
    'England Rugby': '137123',
    'Wales Rugby': '137141',
    'Scotland Rugby': '137136',
    'France Rugby': '137128',
    'Italy Rugby': '137175',
    'South Africa Rugby': '137137',
}

ROUND_CODES = {
    '125': 'Quarter-Final',
    '150': 'Semi-Final',
    '160': 'Playoff',
    '170': 'Playoff Semi-Final',
    '180': 'Playoff Final',
    '200': 'Final',
    '500': 'Pre-Season',
}

if 'ch_monitored' not in st.session_state:
    st.session_state.ch_monitored = False


def progress_callback(current, total, message):
    st.session_state.pbar.progress(current / total, message)


async def get_topics_from_db():
    data = await DBHelper(st.session_state.db_url).list_records(Topic)
    st.session_state.topics = data


def monitor_callback():
    if st.session_state.ch_monitored:
        remove_monitored(st.session_state.selected_topic.topic_name,
                         st.session_state.db_url)
    else:
        add_monitored(st.session_state.selected_topic.topic_name,
                      st.session_state.db_url,
                      st.session_state.root_dl_path)


def display_channel(channel, tab):
    col_cont = tab.container(border=True)
    col1, col2 = col_cont.columns([.1, 1])
    if channel.logo:
        col1.image(channel.logo, width=100)
    else:
        col1.title(':material/privacy_tip:')
    col2.title(channel.ch_name)
    col_cont.divider()
    if not st.session_state.topics:
        asyncio.run(get_topics_from_db())
    if not st.session_state.topics:
        get = st.button('Get Topics from Telegram?')
        tgc = TGAccount(st.session_state.api_id,
                        st.session_state.api_hash,
                        st.session_state.phone)
        dbh = DBHelper(st.session_state.db_url)
        if get:
            asyncio.run(pull_topics(tgc, dbh, channel_name=channel.ch_name,
                                    callback=progress_callback))
            st.rerun()
    topics = st.session_state.topics
    topic_list = sorted([topic.topic_name for topic in topics])

    col1, col2 = col_cont.columns([.6, .4])
    topic_sel = col1.selectbox('Choose Topic',
                               topic_list,
                               index=None)

    if topic_sel:
        is_mon = is_monitored(topic_sel, st.session_state.db_url)
        st.session_state.ch_monitored = is_mon
        monitor_topic = col2.checkbox('Monitor Topic',
                                      value=is_mon,
                                      on_change=monitor_callback)
    if topic_sel:
        tab1, tab2 = col_cont.tabs(['League', 'Teams'])
        draw_league(tab1, topic_sel, topics)
        draw_team(tab2, topic_sel, topics)


def draw_players(cont, team_name, team_id):
    players_tab = cont.container(border=True)
    sdb_client = SportsDBClient(st.session_state.sportsdb_api)

    players = sdb_client.search_player_by_name_or_team(team=team_name)

    if players.status_code == 200 and players.json()['player']:
        player_list = [player['strPlayer'] for player in
                       players.json()['player']]
        player = players_tab.selectbox('Choose Player',
                                       player_list, index=None)

        if player:
            for p in players.json()['player']:
                if p['strPlayer'] == player:
                    sel_player = p
                    break
            col1, col2 = players_tab.columns([.2, 1])
            img = sel_player['strCutout'] if sel_player[
                'strCutout'] else sel_player['strThumb']
            if img:
                col1.image(img, width=200)
            else:
                col1.write('No Image')
            col2.title(sel_player['strPlayer'])
            desc = sel_player['strDescriptionEN'] if sel_player[
                'strDescriptionEN'] else 'No Description'
            col2.text_area("Description", desc, height=200)
            cont = players_tab.container(border=True)
            cont.subheader('Player Details')
            player_stats = {}
            for key, value in sel_player.items():
                if (key == 'strDescriptionEN' or
                        'id' in key):
                    continue
                if value:
                    player_stats[key.replace('str', '')] = value

            cont.table(player_stats)


def draw_old_events(cont, team_id):
    sdb_client = SportsDBClient(st.session_state.sportsdb_api)
    old_events = sdb_client.get_last_events_by_team(team_id)
    if old_events.status_code == 200:
        cont.subheader('Past Events:')
        results = {}
        for event in old_events.json()['results']:
            if event['intRound'] in ROUND_CODES:
                rnd = ROUND_CODES[event['intRound']]
            else:
                rnd = event['intRound']
            league_id = event['idLeague']
            league = sdb_client.lookup_league_by_id(league_id)
            league_name = league.json()['leagues'][0]['strLeague']

            results[event['strEvent']] = {
                'league': league_name,
                'thumb': event['strThumb'],
                'date': event['dateEvent'],
                'time': event['strTime'],
                'venue': event['strVenue'],
                'round': rnd,
                'home_team': event['strHomeTeam'],
                'home_score': event['intHomeScore'],
                'away_team': event['strAwayTeam'],
                'away_score': event['intAwayScore'],
            }
        # Convert to a dataframe
        df = pd.DataFrame(results).transpose()
        dfe = cont.data_editor(df,
                               column_config={
                                   'thumb':
                                       st.column_config.ImageColumn(
                                           "Thumbnail",
                                           help="Event Thumbnail"
                                       ),
                               },
                               )


def draw_new_events(cont, team_id):
    sdb_client = SportsDBClient(st.session_state.sportsdb_api)
    new_events = sdb_client.get_next_events_by_team(team_id)

    if new_events.status_code == 200:
        cont.subheader('Upcoming Team Events:')
        results = {}
        if new_events.json()['events']:
            for event in new_events.json()['events']:
                if event['intRound'] in ROUND_CODES:
                    rnd = ROUND_CODES[event['intRound']]
                else:
                    rnd = event['intRound']
                results[event['strEvent']] = {
                    'thumb': event['strThumb'],
                    'date': event['dateEvent'],
                    'time': event['strTime'],
                    'venue': event['strVenue'],
                    'round': rnd,
                    'home_team': event['strHomeTeam'],
                    'away_team': event['strAwayTeam'],
                }
            # Convert to a dataframe
            df = pd.DataFrame(results).transpose()
            dfe = cont.data_editor(df,
                                   column_config={
                                       'thumb':
                                           st.column_config.ImageColumn(
                                               "Thumbnail",
                                               help="Event Thumbnail"
                                           ),
                                   },
                                   )
    else:
        cont.write(new_events.text)


def draw_team(cont, topic_sel, topics):
    if st.session_state.teams:
        data = st.session_state.teams
        team_name_list = [team['strTeam'] for team in data]
        team = cont.selectbox('Choose Team',
                              team_name_list, index=None)
        sel_team = None
        if team in TEAM_IDS:
            team_id = TEAM_IDS[team]
            sdb_client = SportsDBClient(st.session_state.sportsdb_api)
            sel_team = sdb_client.lookup_team_by_id(team_id)
            sel_team = sel_team.json()['teams'][0]

        else:
            for t in data:
                if t['strTeam'] == team:
                    sel_team = t
                    break
        if team:
            cont.image(sel_team['strBadge'], width=150)
            cont.markdown(f"""
                | Year Formed | Stadium | Location | Website |
                |-------------|---------|----------|---------|
                | {sel_team['intFormedYear']} | {sel_team['strStadium']} | {sel_team['strLocation']} | {sel_team['strWebsite']} |
                """)

            cont.write(sel_team['strDescriptionEN'])
            if sel_team['strEquipment']:
                cont.image(sel_team['strEquipment'], width=150)
            if sel_team['strBanner']:
                cont.image(sel_team['strBanner'], width=150)
            cont.markdown(sel_team['strYoutube'])

            cont.divider()
            players_tab, past_tab, next_tab = cont.tabs(['Players', 'Past '
                                                                    'Events',
                                                         'Upcoming Events'])

            draw_players(players_tab, sel_team['strTeam'], sel_team['idTeam'])
            draw_old_events(past_tab, sel_team['idTeam'])
            draw_new_events(next_tab, sel_team['idTeam'])
    else:
        cont.write("No teams found")
        st.stop()


def draw_league(cont, topic_sel, topics):
    topic_detail_cont = cont.container(border=True)
    topic = [topic for topic in topics if topic.topic_name == topic_sel][0]
    if topic:
        st.session_state.selected_topic = topic
    topic_detail_cont.subheader(topic.topic_name)
    if topic.topic_name in TOPIC_NAMES:
        name = TOPIC_NAMES[topic.topic_name]
    else:
        name = topic.topic_name
    sdb_client = SportsDBClient(st.session_state.sportsdb_api)
    data = sdb_client.list_teams_in_league(name)
    league_id = None
    league_detail = None
    if data.json()['teams']:
        for team in data.json()['teams']:
            if team['idLeague']:
                league_id = team['idLeague']
                break
    if league_id:
        try:
            league_detail = sdb_client.lookup_league_by_id(league_id)
            league_detail = league_detail.json()['leagues'][0]
        except KeyError:
            topic_detail_cont.write("League not found")
            st.stop()
    else:
        try:
            league_id = LEAGUE_IDS[name]
            league_detail = sdb_client.lookup_league_by_id(LEAGUE_IDS[name])
            league_detail = league_detail.json()['leagues'][0]
        except KeyError:
            topic_detail_cont.write("No league found")

    if data.status_code == 200:
        if data.json()['teams']:
            st.session_state.teams = data.json()['teams']
        else:
            try:
                data = sdb_client.list_all_teams_in_league_by_l_id(league_id)
                if data.json()['teams']:
                    st.session_state.teams = data.json()['teams']

            except KeyError:
                topic_detail_cont.write("No league found")
                st.stop()

    topic_detail_cont.image(league_detail['strLogo'],
                            width=800)

    topic_detail_cont.markdown(f"""
            | Name | Country | Sport | Website |
            |------|---------|-------|---------|
            | {league_detail['strLeague']} | {league_detail['strCountry']} | {league_detail['strSport']} | {league_detail['strWebsite']} |
            """)
    topic_detail_cont.write(league_detail['strDescriptionEN'])
    col1, col2 = topic_detail_cont.columns([.8, .2])
    if league_detail['strBanner']:
        col1.image(league_detail['strBanner'],
                   width=800)
    if league_detail['strTrophy']:
        col2.image(league_detail['strTrophy'],
                   width=150, caption='Trophy')

    col1, col2 = topic_detail_cont.columns([.1, 1])
    if league_detail['strBadge']:
        col1.image(league_detail['strBadge'],
                   width=100, caption='Badge')

    past_tab, next_tab = col2.tabs(['Past Events', 'Upcoming Events'])
    schedule = sdb_client.get_next_events_by_league(league_id)
    # past_games = sdb_client.get_league_events_by_season(league_id,
    #                                                     '2023-2024')
    seasons = sdb_client.list_all_seasons_in_league(league_id)
    season_list = [season['strSeason'] for season in seasons.json()['seasons']]
    season = past_tab.selectbox('Choose Season', season_list, index=None)
    if season:
        past_games = sdb_client.get_league_events_by_season(league_id, season)
        season_final = None
        for i in past_games.json()['events']:
            if i['intRound'] == '200':
                season_final = i
                break
        if season_final:
            winner = season_final['strHomeTeam'] if season_final[
                                                        'intHomeScore'] > \
                                                    season_final[
                                                        'intAwayScore'] else \
                season_final['strAwayTeam']
            winner_detail = sdb_client.search_team_by_name(winner)
            winner_detail = winner_detail.json()['teams'][0]
            winner_logo = (f"![Winner Logo]("
                           f"{winner_detail['strBadge']}/tiny)")
            score = f"{season_final['intHomeScore']} - {season_final['intAwayScore']}"
            venue = season_final['strVenue']
            date = season_final['dateEvent']
            past_tab.markdown(f"""
            | {season} Winner |  Venue | Date | Score |
            |-----------------|--------|------|-------|
            | {winner_logo}{winner} | {venue} | {date} | {score} |
            """)
        # with open('data.json', 'w') as f:
        #     f.write(json.dumps(past_games.json(), indent=4))
        if past_games.status_code == 200:
            past_tab.subheader('Past League Events:')
            results = {}

            for event in past_games.json()['events']:
                if event['intRound'] in ROUND_CODES:
                    rnd = ROUND_CODES[event['intRound']]
                else:
                    rnd = event['intRound']
                results[event['strEvent']] = {
                    'thumb': event['strThumb'],
                    'date': event['dateEvent'],
                    'time': event['strTime'],
                    'round': rnd,
                    'home_team_logo': event['strHomeTeamBadge'],
                    'home_team': event['strHomeTeam'],
                    'away_team_logo': event['strAwayTeamBadge'],
                    'away_team': event['strAwayTeam'],
                    'home_score': event['intHomeScore'],
                    'away_score': event['intAwayScore'],
                    'video': event['strVideo'],

                }
            # Convert to a dataframe
            df = pd.DataFrame(results).transpose()
            dfe = past_tab.data_editor(df,
                                       column_config={
                                           'thumb':
                                               st.column_config.ImageColumn(
                                                   "Thumbnail",
                                                   help="Event Thumbnail"
                                               ),
                                           'video':
                                               st.column_config.LinkColumn(
                                                   "Video",
                                                   help="Event Video",
                                                   display_text="Watch Video", ),
                                           'home_team_logo':
                                               st.column_config.ImageColumn(
                                                   "Home Team Logo",
                                                   help="Home Team Logo",
                                                   width='small'
                                               ),
                                           'away_team_logo':
                                               st.column_config.ImageColumn(
                                                   "Away Team Logo",
                                                   help="Away Team Logo",
                                                   width='small'
                                               ),
                                       },
                                       )
        else:
            past_tab.write(past_games.text)

    if schedule.status_code == 200 and schedule.json()['events']:
        next_tab.subheader('Upcoming League Events:')
        results = {}
        for event in schedule.json()['events']:
            if event['intRound'] in ROUND_CODES:
                rnd = ROUND_CODES[event['intRound']]
            else:
                rnd = event['intRound']
            results[event['strEvent']] = {
                'thumb': event['strThumb'],
                'date': event['dateEvent'],
                'time': event['strTime'],
                'round': rnd,
                'home_team': event['strHomeTeam'],
                'away_team': event['strAwayTeam'],
            }
        # Convert to a dataframe
        df = pd.DataFrame(results).transpose()
        dfe = next_tab.data_editor(df,
                                   column_config={
                                       'thumb':
                                           st.column_config.ImageColumn(
                                               "Thumbnail",
                                               help="Event Thumbnail"
                                           ),
                                   },
                                   )

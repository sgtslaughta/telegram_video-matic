import streamlit as st
from .sportsDB import SportsDBClient
from .db_utils import DBHelper, TelegramChannel, Topic
from .data_utils import TGAccount
import pandas as pd
import asyncio
import json

db_url = "postgresql+asyncpg://user:password@localhost:5432/moviesdb"
topic_names = {
    'Gallagher Premiership': 'English Premiership Rugby',
    'URC': 'United Rugby Championship',
    '6 Nations': 'Six Nations Championship',
    'Top 14': 'French Top 14',
    '2019 World Cup': 'Rugby World Cup',
    'Super Rugby Americas': 'Super Liga Americana',
    'The Rugby Championship': 'Rugby Championship',
    'Pro D2': 'French Pro D2',
}

async def get_topics_from_db():
    data = await DBHelper(db_url).list_records(Topic)
    st.session_state.topics = data

def display_channel(channel):
    col_cont = st.container(border=True)
    col1, col2 = col_cont.columns([.1, 1])
    if channel.logo:
        col1.image(channel.logo, width=100)
    else:
        col1.title(':material/privacy_tip:')
    col2.title(channel.ch_name)
    col_cont.divider()
    if not st.session_state.topics:
        asyncio.run(get_topics_from_db())
    topics = st.session_state.topics
    topic_list = sorted([topic.topic_name for topic in topics])



    topic_sel = col_cont.selectbox('Choose Topic',
                                   topic_list,
                                   index=None)
    if topic_sel:
        tab1, tab2 = col_cont.tabs(['League', 'Teams'])
        draw_league(tab1, topic_sel, topics)
        draw_team(tab2, topic_sel, topics)


def draw_team(cont, topic_sel, topics):
        if st.session_state.teams:
            data = st.session_state.teams
            team_name_list = [team['strTeam'] for team in data]
            team = cont.selectbox('Choose Team',
                                               team_name_list, index=None)
            if team:
                for t in data:
                    if t['strTeam'] == team:
                        sel_team = t
                        break
                # print(sel_team)
                try:

                    cont.image(sel_team['strBadge'], width=150)
                    cont.markdown(f"""
                    | Year Formed | Stadium | Location | Website |
                    |-------------|---------|----------|---------|
                    | {sel_team['intFormedYear']} | {sel_team['strStadium']} | {sel_team['strLocation']} | {sel_team['strWebsite']} |
                    """)

                    cont.write(sel_team['strDescriptionEN'])
                    cont.image(sel_team['strEquipment'], width=150)
                    cont.image(sel_team['strBanner'], width=150)
                    # print(sel_team['strYoutube'])
                    cont.markdown(sel_team['strYoutube'])

                    cont.divider()
                    ##############################

                    players_tab, past_tab, next_tab = cont.tabs([
                        'Players', 'Past '
                                                                 'Events', 'Upcoming Events'])
                    next_tab.subheader('Upcoming Team Events:')
                    sdb_client = SportsDBClient(st.session_state.sportsdb_api)
                    team_details = sdb_client.lookup_team_by_id(sel_team[
                                                                    'idTeam'])
                    new_events = sdb_client.get_next_events_by_team(sel_team[
                                                                 'idTeam'])
                    old_events = sdb_client.get_last_events_by_team(sel_team[
                                                                 'idTeam'])
                    players = sdb_client.lookup_players_by_team(sel_team[
                                                                    'idTeam'])
                    if players.status_code == 200:
                        print(json.dumps(players.json(), indent=4))
                        player_list = [player['strPlayer'] for player in players.json()['player']]
                        player = players_tab.selectbox('Choose Player',
                                                         player_list, index=None)
                        if player:
                            for p in players.json()['player']:
                                if p['strPlayer'] == player:
                                    sel_player = p
                                    break
                            # print(sel_player)
                            col1, col2 = players_tab.columns([.2, 1])
                            col1.image(sel_player['strCutout'], width=200)
                            col2.title(sel_player['strPlayer'])
                            col2.text_area("Description", sel_player[
                                'strDescriptionEN'], height=200)
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
                    # print(players.json())
                    if new_events.status_code == 200:
                        results = {}
                        for event in new_events.json()['events']:
                            results[event['strEvent']] = {
                                'thumb': event['strThumb'],
                                'date': event['dateEvent'],
                                'time': event['strTime'],
                                'venue': event['strVenue'],
                                'round': event['intRound'],
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
                    else:
                        next_tab.write(new_events.text)
                    if old_events.status_code == 200:
                        results = {}
                        for event in old_events.json()['results']:
                            results[event['strEvent']] = {
                                'thumb': event['strThumb'],
                                'date': event['dateEvent'],
                                'time': event['strTime'],
                                'venue': event['strVenue'],
                                'round': event['intRound'],
                                'home_team': event['strHomeTeam'],
                                'away_team': event['strAwayTeam'],
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
                                                         },
                                                           )
                    # schedule = (
                    #     sdb_client.get_schedule_next_events_by_league(
                    #         sel_team['idLeague']))
                    # print(schedule.json())
                    # topic_detail_cont.write(schedule.json())
                except BaseException as e:
                    pass

def draw_league(cont, topic_sel, topics):

    topic_detail_cont = cont.container(border=True)
    topic = [topic for topic in topics if topic.topic_name == topic_sel][0]
    if topic:
        st.session_state.selected_topic = topic
    topic_detail_cont.subheader(topic.topic_name)
    # tg = TGAccount(st.session_state.api_id,
    #                st.session_state.api_hash,
    #                st.session_state.phone)
    # top_messages = asyncio.run(tg.get_messages(entity=channel.chat,
    #                                            limit=10,
    #                                            reply_to=topic.topic_id))
    # for msg in top_messages:
    #     topic_detail_cont.write(msg)
    if topic.topic_name in topic_names:
        name = topic_names[topic.topic_name]
    else:
        name = topic.topic_name
    sdb_client = SportsDBClient(st.session_state.sportsdb_api)
    data = sdb_client.list_teams_in_league(name)
    if data.json():
        st.session_state.teams = data.json()['teams']
    league_id = data.json()['teams'][0]['idLeague']
    league_detail = sdb_client.lookup_league_by_id(league_id)
    topic_detail_cont.image(league_detail.json()['leagues'][0]['strBadge'],
                            width=150)
    league_detail = league_detail.json()['leagues'][0]
    topic_detail_cont.markdown(f"""
            | Name | Country | Sport | Website |
            |------|---------|-------|---------|
            | {league_detail['strLeague']} | {league_detail['strCountry']} | {league_detail['strSport']} | [Website]({league_detail['strWebsite']}) |
            """)
    topic_detail_cont.write(league_detail['strDescriptionEN'])

    past_tab, next_tab = topic_detail_cont.tabs(['Past Events', 'Upcoming Events'])
    schedule = sdb_client.get_next_events_by_league(league_id)
    # past_games = sdb_client.get_league_events_by_season(league_id,
    #                                                     '2023-2024')
    seasons = sdb_client.list_all_seasons_in_league(league_id)
    season_list = [season['strSeason'] for season in seasons.json()['seasons']]
    season = past_tab.selectbox('Choose Season', season_list, index=None)
    if season:
        past_games = sdb_client.get_league_events_by_season(league_id, season)
        if past_games.status_code == 200:
            past_tab.subheader('Past League Events:')
            results = {}

            for event in past_games.json()['events']:
                results[event['strEvent']] = {
                    'thumb': event['strThumb'],
                    'date': event['dateEvent'],
                    'time': event['strTime'],
                    'round': event['intRound'],
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
                                             display_text="Watch Video",),
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
            results[event['strEvent']] = {
                'thumb': event['strThumb'],
                'date': event['dateEvent'],
                'time': event['strTime'],
                'round': event['intRound'],
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




    # fb_icon = "https://img.icons8.com/color/48/facebook-new.png"
    # tw_icon = "https://img.icons8.com/color/48/twitter--v1.png"
    # inst_icon = "https://img.icons8.com/fluency/48/instagram-new.png"
    # yt_icon = "https://img.icons8.com/color/48/youtube-play.png"
    #
    # fb_link = str(league_detail['strFacebook'])
    # topic_detail_cont.html(f"<a href='"
    #                        f"{fb_link}' "
    #                        f"target='_blank'><img "
    #                        f"src='{fb_icon}'></a>")
    #
    # topic_detail_cont.markdown(f"""
    #         [![Title]({fb_icon})]({league_detail['strFacebook']})
    #         [![Title]({tw_icon})]({league_detail['strTwitter']})
    #         [![Title]({inst_icon})]({league_detail['strInstagram']})
    #         [![Title]({yt_icon})]({league_detail['strYoutube']})
    #         """, unsafe_allow_html=True)
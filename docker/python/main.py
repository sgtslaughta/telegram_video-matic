from utils.db_utils import DBHelper, TelegramChannel, Topic
from utils.data_utils import TGAccount
from utils.sportsDB import SportsDBClient
import thesportsdb as tsdb
# https://github.com/TralahM/thesportsdb
import streamlit as st
from streamlit_marquee import streamlit_marquee as marquee
from streamlit_js_eval import streamlit_js_eval as js
import asyncio

db_url = "postgresql+asyncpg://user:password@localhost:5432/moviesdb"

st.set_page_config(layout='wide',
                   page_icon=':tv:',
                   page_title='Telegram Video Manager')

topic_names = {
    'Gallagher Premiership': 'English Premiership Rugby',
    'URC': 'United Rugby Championship',
    '6 Nations': 'Six Nations Championship',
    'Top 14': 'French Top 14',
    '2019 World Cup': 'Rugby World Cup',
    'Super Rugby Americas': 'Super Liga Americana',
}

def config():
    if 'api_id' not in st.session_state:
        st.session_state.api_id = None
    if 'api_hash' not in st.session_state:
        st.session_state.api_hash = None
    if 'phone' not in st.session_state:
        st.session_state.phone = None
    if 'sportsdb_api' not in st.session_state:
        st.session_state.sportsdb_api = None
    if 'channels' not in st.session_state:
        st.session_state.channels = None
    if 'topics' not in st.session_state:
        st.session_state.topics = None

@st.dialog("Enter Telegram API Details")
def gather_tg_details():
    api_val = st.session_state.api_id
    hash_val = st.session_state.api_hash
    phone_val = st.session_state.phone
    api = st.text_input('API ID',
                        value=api_val,
                        help='Get your API ID from https://my.telegram.org')
    hash = st.text_input('API Hash',
                         value=hash_val,
                         help='Get your API Hash from '
                               'https://my.telegram.org')
    phone = st.text_input('Phone Number',
                          value=phone_val,
                          help=('Enter your phone number with '
                                          'country code'))
    sportsdb_api = st.text_input('SportsDB API Key',
                                    help='Get your API key from https://www.thesportsdb.com/api.php')
    if st.button('Submit') and api and hash and phone:
        st.session_state.api_id = api
        st.session_state.api_hash = hash
        st.session_state.phone = phone
        st.session_state.sportsdb_api = sportsdb_api
        st.rerun()


def menu(cont):
    button_cont = cont.container(border=True, height=500)
    button_cont.button('Click Me', use_container_width=True)
    button_cont.button(':material/key: API Information',
                       use_container_width=True,
                       on_click=gather_tg_details)

def make_marguee(text=None):
    if text:
        # Get the width of the screen
        width = js(js_expressions='window.innerWidth')
        ops = {
            'content': text,
            'width': width,
            'lineHeight': 1,
            'background': "transparent",
            'animationDuration': '30s',
        }
        marquee(**ops)

def core():
    # make_marguee("Welcome to the Telegram Video Manager")
    img_col, title_col = st.columns([1, 5])
    img_col.image('https://media.tenor.com/9ZsRZ-PXPlwAAAAi/telegram-gif.gif',
            width=100)
    title_col.title(':green[:material/movie:] :blue[Telegram] Video Manager',
                    help='Manage your videos with ease.')
    col_a, col_b = st.columns([1, 5])
    menu(col_a)
    tab1, tab2 = col_b.tabs(['Main Tabs', 'Other Tabs'])
    choose_channel(tab1)

def load_page():
    config()
    if (not st.session_state.api_id
            or not st.session_state.api_hash
            or not st.session_state.phone):
        gather_tg_details()
    else:
        core()

async def get_channels_from_db():

    data = await DBHelper(db_url).list_records(TelegramChannel)
    tg = TGAccount(st.session_state.api_id,
                     st.session_state.api_hash,
                     st.session_state.phone)
    ch_objs = []
    for ch in data:
        ch.chat = await tg.get_channel_full(ch_name_id=ch.ch_name)
        ch.logo = await tg.get_logo_photo(ch.ch_id)
        ch_objs.append(ch)
    st.session_state.channels = ch_objs

async def get_topics_from_db():
    data = await DBHelper(db_url).list_records(Topic)
    st.session_state.topics = data

async def grab_topic(channel, topic_id):
    tg = TGAccount(st.session_state.api_id,
                     st.session_state.api_hash,
                     st.session_state.phone)
    topic = await tg.get_forumntopic(channel, topic_id)
    if topic:
        return topic

async def get_message(channel, msg_id):
    tg = TGAccount(st.session_state.api_id,
                        st.session_state.api_hash,
                        st.session_state.phone)
    msg = await tg.get_messages_by_id(channel_name=channel.ch_name,
                                      msg_id=msg_id)
    return msg

def display_channel(cont, channel):
    col_cont = cont.container(border=True)
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
    col3, col4 = col_cont.columns([.2, 1])
    topic_cont = col3.container(border=True)
    topic_sel = topic_cont.selectbox('Choose Topic',
                                   topic_list,
                                   index=None)
    if topic_sel:
        topic_detail_cont = col4.container(border=True)
        topic = [topic for topic in topics if topic.topic_name == topic_sel][0]
        topic_detail_cont.subheader(topic.topic_name)
        tg = TGAccount(st.session_state.api_id,
                         st.session_state.api_hash,
                         st.session_state.phone)
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
        data = sdb_client.list_teams_in_league(name.strip('The '
                                                                      'the'))

        if data.json()['teams']:
            team_name_list = [team['strTeam'] for team in data.json()['teams']]
            team = topic_detail_cont.selectbox('Choose Team', team_name_list)
            if team:
                for t in data.json()['teams']:
                    if t['strTeam'] == team:
                        sel_team = t
                        break
                print(sel_team)
                try:
                    topic_detail_cont.image(sel_team['strBadge'], width=150)
                    topic_detail_cont.markdown(f"""
                    | Year Formed | Stadium | Location | Website |
                    |-------------|---------|----------|---------|
                    | {sel_team['intFormedYear']} | {sel_team['strStadium']} | {sel_team['strLocation']} | {sel_team['strWebsite']} |
                    """)

                    topic_detail_cont.write(sel_team['strDescriptionEN'])
                    topic_detail_cont.image(sel_team['strEquipment'], width=150)
                    topic_detail_cont.image(sel_team['strBanner'], width=150)
                    print(sel_team['strYoutube'])
                    topic_detail_cont.markdown(sel_team['strYoutube'])
                except BaseException as e:
                    pass






def choose_channel(cont):
    col1, col2, col3 = cont.columns(3)
    if not st.session_state.channels:
        asyncio.run(get_channels_from_db())
    if st.session_state.channels:
        selected_ch = col1.selectbox('Choose Channel',
                                     [ch.ch_name for ch in
                                      st.session_state.channels],
                                     index=None)
        if selected_ch:
            ch = [ch for ch in st.session_state.channels if ch.ch_name == selected_ch][0]
            display_channel(cont, ch)

if __name__ == '__main__':
    load_page()
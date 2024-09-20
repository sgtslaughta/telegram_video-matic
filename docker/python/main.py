from operator import index

from utils.db_utils import DBHelper, TelegramChannel, Topic
from utils.data_utils import TGAccount
from utils.sport_details import display_channel
import thesportsdb as tsdb
# https://github.com/TralahM/thesportsdb
import streamlit as st
from streamlit_marquee import streamlit_marquee as marquee
from streamlit_js_eval import streamlit_js_eval as js
import asyncio
import pandas as pd


db_url = "postgresql+asyncpg://user:password@localhost:5432/moviesdb"

st.set_page_config(layout='wide',
                   page_icon=':tv:',
                   page_title='Telegram Video Manager')


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
    if 'teams' not in st.session_state:
        st.session_state.teams = None
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = None
    if 'selected_topic' not in st.session_state:
        st.session_state.selected_topic = None

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


def menu():
    st.sidebar.button('Click Me', use_container_width=True)
    st.sidebar.button(':material/key: API Information',
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

    img_col, title_col = st.columns([1, 5])
    st.sidebar.image('https://media.tenor.com/9ZsRZ-PXPlwAAAAi/telegram-gif'
                    '.gif',
            width=100)
    st.title(':green[:material/movie:] :blue[Telegram] Video Manager',
                    help='Manage your videos with ease.')
    menu()
    choose_channel()

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



def color_winner_cell(row):
    color_home = 'color: green' if row['home_score'] > row['away_score'] else ''
    color_away = 'color: green' if row['away_score'] > row['home_score'] else ''
    # Return list for both columns
    return [color_home, color_away]




def choose_channel():
    col1, col2, col3 = st.columns(3)
    if not st.session_state.channels:
        asyncio.run(get_channels_from_db())
    if st.session_state.channels:
        selected_ch = col1.selectbox('Choose Channel',
                                     [ch.ch_name for ch in
                                      st.session_state.channels],
                                     index=None)
        if selected_ch:
            ch = [ch for ch in st.session_state.channels if ch.ch_name == selected_ch][0]

            display_channel(ch)

if __name__ == '__main__':
    load_page()
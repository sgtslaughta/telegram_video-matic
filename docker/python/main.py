import asyncio
from os import environ
from time import sleep

import streamlit as st

from utils.log_utils import log

try:
    from utils.db_utils import DBHelper, TelegramChannel, Topic
    from utils.data_utils import TGAccount
    from utils.sport_details import display_channel
    from utils.data_utils import pull_channels, pull_topics
    from utils.file_page import draw_files_page
except Exception as e:
    print(e)
    import os, signal

    os.kill(os.getpid(), signal.SIGKILL)

st.set_page_config(layout='wide',
                   page_icon=':tv:',
                   page_title='Telegram Video Manager')


def create_db_url():
    get_vars()
    try:
        user = environ['DB_USER']
        pw = environ['DB_PASS']
        host = environ['DB_HOST']
        name = environ['DB_NAME']
        port = environ['DB_PORT']
    except KeyError as e:
        log(f"Missing environment variable: {e}", 'error')
        exit(1)
    return f"postgresql+asyncpg://{user}:{pw}@{host}:{port}/{name}"


def get_vars():
    try:
        with open('vars.txt') as f:
            for line in f:
                key, value = line.strip().split('=')
                environ[key] = value
    except Exception as e:
        log(str(e), 'error')


def config():
    if 'init_vars' not in st.session_state:
        st.session_state.init_vars = True
        get_vars()
    if 'db_url' not in st.session_state:
        st.session_state.db_url = create_db_url()
    if 'api_id' not in st.session_state:
        if 'API_ID' in environ:
            st.session_state.api_id = environ['API_ID']
        else:
            st.session_state.api_id = None
    if 'api_hash' not in st.session_state:
        if 'API_HASH' in environ:
            st.session_state.api_hash = environ['API_HASH']
        else:
            st.session_state.api_hash = None
    if 'phone' not in st.session_state:
        if 'PHONE' in environ:
            st.session_state.phone = environ['PHONE']
        else:
            st.session_state.phone = None
    if 'sportsdb_api' not in st.session_state:
        if 'SDB_API' in environ:
            st.session_state.sportsdb_api = environ['SDB_API']
        else:
            st.session_state.sportsdb_api = None
    if 'root_dl_path' not in st.session_state:
        if 'ROOT_DL_PATH' in environ:
            st.session_state.root_dl_path = environ['ROOT_DL_PATH']
        else:
            st.session_state.root_dl_path = '/monitored'
    if 'channels' not in st.session_state:
        st.session_state.channels = None
    if 'topics' not in st.session_state:
        st.session_state.topics = None
    if 'teams' not in st.session_state:
        st.session_state.teams = None
    if 'selected_channel' not in st.session_state:
        st.session_state.selected_channel = None
    if 'selected_team' not in st.session_state:
        st.session_state.selected_team = None
    if 'selected_topic' not in st.session_state:
        st.session_state.selected_topic = None
    if 'pbar' not in st.session_state:
        st.session_state.pbar = st.progress(0)
    if 'channel_changed' not in st.session_state:
        st.session_state.channel_changed = False
    if 'var_name' not in st.session_state:
        st.session_state.var_name = 'Telegram'


@st.dialog("Enter Telegram API Details")
def gather_tg_details():
    api_val = st.session_state.api_id
    hash_val = st.session_state.api_hash
    phone_val = st.session_state.phone
    sdb_api = st.session_state.sportsdb_api
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
                                 help='Get your API key from '
                                      'https://www.thesportsdb.com/api.php',
                                 value=sdb_api)
    if st.button('Submit') and api and hash and phone:
        st.session_state.api_id = api
        st.session_state.api_hash = hash
        st.session_state.phone = phone
        st.session_state.sportsdb_api = sportsdb_api
        st.rerun()


async def get_channels_from_db():
    dbh = DBHelper(st.session_state.db_url)
    data = await dbh.list_records(TelegramChannel)
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
    color_home = 'color: green' if row['home_score'] > row[
        'away_score'] else ''
    color_away = 'color: green' if row['away_score'] > row[
        'home_score'] else ''
    # Return list for both columns
    return [color_home, color_away]


def progress_callback(current, total, message):
    st.session_state.pbar.progress(current / total, message)


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
            st.session_state.var_name = selected_ch
            ch = [ch for ch in st.session_state.channels if
                  ch.ch_name == selected_ch][0]
            st.session_state.selected_channel = ch
            info_tab, files_tab = st.tabs(['Channel Info', 'Files'])
            display_channel(ch, info_tab)
            draw_files_page(files_tab)

    else:
        st.write('No channels found in the database...')
        get = st.button('Populate from Telegram?')
        if get:
            tgh = TGAccount(st.session_state.api_id,
                            st.session_state.api_hash,
                            st.session_state.phone)
            dbh = DBHelper(st.session_state.db_url)
            asyncio.run(pull_channels(tgh, dbh, progress_callback))
            sleep(1)
            st.rerun()


def menu():
    st.sidebar.button('Click Me', use_container_width=True)
    st.sidebar.button(':material/key: API Information',
                      use_container_width=True,
                      on_click=gather_tg_details)


def load_page():
    config()
    if (not st.session_state.api_id
            or not st.session_state.api_hash
            or not st.session_state.phone):
        gather_tg_details()
        st.write('Please enter your Telegram API details to continue...')
        st.button('Refresh')
    else:
        img_col, title_col = st.columns([1, 5])
        st.sidebar.image(
            'https://media.tenor.com/9ZsRZ-PXPlwAAAAi/telegram-gif'
            '.gif',
            width=100)
        var_name = st.session_state.var_name
        st.title(f':green[:material/movie:] :blue[{var_name}] Video Manager',
                 help='Manage your videos with ease.')
        menu()
        choose_channel()


if __name__ == '__main__':
    load_page()

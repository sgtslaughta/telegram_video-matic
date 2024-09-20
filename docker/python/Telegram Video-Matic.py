import base64
from sys import thread_info

import os

from altair.vegalite.v5.theme import theme
from pygments.styles.dracula import background
from streamlit_elements import elements, html, mui, dashboard, editor, lazy, sync
from utils.db_utils import TelegramChannel, Topic, Message
from utils.tg_utils import TGAccount
from utils.db_utils import DBHelper
from utils import data_utils as du
from sqlalchemy import or_
import streamlit as st
import asyncio
import pandas as pd
import time
from utils.data_utils import show_tags

db_url = "postgresql+asyncpg://user:password@localhost:5432/moviesdb"
st.set_page_config(page_title="Telegram Video-Matic", page_icon=":tv:", layout="wide")


def setup():
    if 'api_id' not in st.session_state:
        st.session_state.api_id = None
    if 'api_hash' not in st.session_state:
        st.session_state.api_hash = None
    if 'phone' not in st.session_state:
        st.session_state.phone = None
    if 'channels' not in st.session_state:
        st.session_state.channels = None
    if 'topics' not in st.session_state:
        st.session_state.topics = None
    if 'channel_select' not in st.session_state:
        st.session_state.channel_select = None
    if 'topic_select' not in st.session_state:
        st.session_state.topic_select = None
    if 'videos' not in st.session_state:
        st.session_state.videos = None
    if "dl_path" not in st.session_state:
        st.session_state.dl_path = None
    if "adding_dl_path" not in st.session_state:
        st.session_state.adding_dl_path = False
    if 'pbar' not in st.session_state:
        st.session_state.pbar = st.progress(0)
    if 'dbh' not in st.session_state:
        st.session_state.dbh = False


def set_dl_path(path):
    st.session_state.dl_path = path
    st.session_state.adding_dl_path = False


def folder_selector(folder_path='.'):
    try:
        with st.form(key='folder_selector'):
            # Ensure folder_path is a valid directory
            if not os.path.isdir(folder_path):
                st.error('Invalid folder path')
                return None
            filenames = os.listdir(folder_path)
            folder_names = [f"{folder_path}{f}" if folder_path == '/' else
                            f"{folder_path}/{f}" for f in filenames
                            if os.path.isdir(os.path.join(folder_path, f))]
            folder_names.sort()
            selected_folder = st.selectbox('Select a folder', folder_names, index=0)
            print(f"Selected folder: {selected_folder}")
            clicked = st.form_submit_button('Select', on_click=set_dl_path, args=[selected_folder])
            if clicked:
                print(f"CLICKED")
    except FileNotFoundError:
        st.write("Folder not found.")
        return None


def how_to():
    st.sidebar.image("img/telegram-logo.webp")
    sb = st.sidebar.expander("How to use", expanded=False)
    sb.title("Telegram Video-Matic")
    sb.markdown("This is a Streamlit app connects to a Telegram chat, then will look for "
                "un-downloaded videos and download them to a specified folder.")

    sb.markdown("## Setup")
    sb.markdown("1. Create a Telegram bot and get the API token.")
    sb.markdown("2. Create a Telegram chat and add the bot as an admin.")
    sb.markdown("3. Create a Telegram channel and add the chat as an admin.")
    sb.markdown("4. Create a folder to store the downloaded videos.")
    sb.markdown("5. Enter the required information below and click the 'Start' button.")


def set_apis(api_id, api_hash, phone_num):
    st.session_state.api_id = api_id
    st.session_state.api_hash = api_hash
    st.session_state.phone = phone_num


def api_entry():
    api_id = st.sidebar.text_input("API ID")
    api_hash = st.sidebar.text_input("API Hash")
    phone_num = st.sidebar.text_input("Phone Number")
    tok_len = True if len(api_id) == 8 and api_id.isdigit() else False
    hash_len = True if len(api_hash) == 32 and api_hash.isalpha() else False
    is_filled = True if not tok_len or not api_hash or not phone_num else False
    submit_apis = st.sidebar.button("Submit API",
                                    key="submit_apis",
                                    disabled=is_filled,
                                    on_click=set_apis,
                                    args=[api_id, api_hash, phone_num])


async def get_channels_from_tg():
    tg = TGAccount(api_id=st.session_state.api_id,
                   api_hash=st.session_state.api_hash,
                   phone=st.session_state.phone)
    await du.pull_channels(tg, st.session_state.dbh)


async def get_channels_from_db():
    data = await DBHelper(db_url).list_records(TelegramChannel)
    st.session_state.channels = data

async def get_topics_from_tg():
    tg = TGAccount(api_id=st.session_state.api_id,
                   api_hash=st.session_state.api_hash,
                   phone=st.session_state.phone)
    dbh = DBHelper(db_url)
    await du.pull_topics(tg, dbh,
                         channel_id=st.session_state.channel_select.ch_id,
                         callback=progress_callback)
    db_channel_id = st.session_state.channel_select.ch_id
    stmt = or_(Topic.tg_ch_id == db_channel_id)
    st.session_state.topics = await DBHelper(db_url).query_with_filter(Topic, stmt)

async def get_topics_from_db():
    data = await DBHelper(db_url).list_records(Topic)
    st.session_state.topics = data
    print(data)

async def get_videos():
    topic_id = st.session_state.topic_select[0][0]
    q_str = f"SELECT id FROM topic WHERE topic_id={topic_id}"
    query = f"SELECT * FROM message WHERE topic_id={topic_id}"
    st.session_state.videos = await st.session_state.dbh.execute_db_command(
        query)


def base64_to_image(base64_str):
    """
    Converts a base64 string to an image.
    Args:
        base64_str:

    Returns:

    """
    # Decode hex string to binary data
    return f'data:image/jpeg;base64,{base64_str}'


def get_tags(msg_id):
    return show_tags(db_url, msg_id)


def progress_callback(current, total, message):
    st.session_state.pbar.progress(current / total, message)


async def pull_videos_from_tg():
    dbh = DBHelper(db_url)
    tg_account = TGAccount(api_id=st.session_state.api_id,
                           api_hash=st.session_state.api_hash,
                           phone=st.session_state.phone)
    await du.pull_channels(tg_account, dbh, callback=progress_callback)
    st.session_state.channels = await dbh.list_records(TelegramChannel)


async def download_videos(message_list, contiainer=None):
    tg = TGAccount(api_id=st.session_state.api_id, api_hash=st.session_state.api_hash, phone='+17623334995')
    msgs = await tg.get_messages_by_id(message_list, st.session_state.channel_select[1])
    await tg.multi_download(msgs)


def draw_path_select():
    with st.expander("Download Path", expanded=True):
        st.write("Download path: ", st.session_state.dl_path)
        choose_dl_path = st.button("Choose Download Path")
        if choose_dl_path or st.session_state.adding_dl_path:
            st.session_state.adding_dl_path = True
            path = st.text_input("Enter the path to download the videos.")
            if path:
                folder_selector(path)
                st.session_state.adding_dl_path = False


def make_folder(path, name):
    try:
        if not name:
            st.error("Please enter a folder name.")
            return
        path = f"{path}/{name}"
        os.mkdir(path)
        st.sidebar.success(f"Folder created at {path}")
        st.session_state.dl_path = path
    except Exception as e:
        st.write(f"Error {e}")

def init_db():
    asyncio.run(DBHelper(db_url).create_tables())

def main():
    setup()
    how_to()
    api_entry()
    if st.session_state.api_id and st.session_state.api_hash and st.session_state.phone:
        init_db()
        show_page()

def make_dashboard():
    from streamlit_file_browser import st_file_browser
    event = st_file_browser(path='.',
                    show_download_file=True,
                    show_preview=False,
                    show_choose_file=True)
    if event:
        try:
            print(event)
            create_time = event['target']['create_time']
            # convert the timestamp to datetime
            timestamp_s = create_time / 1000.0
            import datetime
            datetime = datetime.datetime.fromtimestamp(timestamp_s)
            col1, col2 = st.columns(2)
            col1.date_input("Date", value=datetime.date())
            col2.time_input("Time", value=datetime.time())
            # get cwd and combine with event path to get full path
            path = os.getcwd() + '/' + event['target']['path']
            print(path)
            data = open(path, 'rb').read()
            st.download_button(label="Download", file_name=event['target']['path'], data=data)
        except KeyError:
            pass

def show_page():
    make_dashboard()
    if st.session_state.dbh is False:
        asyncio.run(DBHelper(db_url).create_tables())
        st.session_state.dbh = True
    if st.session_state.channels is None:
        asyncio.run(get_channels_from_db())

    st.title("Telegram Video-Matic")
    st.write("Welcome to the Telegram Video-Matic app.")
    col1, col2 = st.columns(2)

    #draw_path_select()
    with col1.expander(f"Download path: :blue[{st.session_state.dl_path}]", expanded=st.session_state.adding_dl_path):
        st.session_state.adding_dl_path = True
        cur_path = st.session_state.dl_path
        if cur_path is None:
            cur_path = '/tmp'
        folder_path = st.text_input("Enter the path to download the videos.", value=cur_path)
        if folder_path != '/' and folder_path:
            folder_path = folder_path.rstrip('/')
        if os.path.isdir(folder_path):
            filenames = os.listdir(folder_path)
            folder_names = [f"{folder_path}{f}" if folder_path == '/' else
                            f"{folder_path}/{f}" for f in filenames
                            if os.path.isdir(os.path.join(folder_path, f))]
            folder_names.sort()
            if folder_names:
                selected_folder = st.selectbox('Select a folder', folder_names, index=0)
            else:
                selected_folder = folder_path
            colx, coly = st.columns(2)
            colx.button("Set Path", on_click=set_dl_path, args=[selected_folder], use_container_width=True)
            with coly.popover("Make Folder Here", use_container_width=True):
                name = st.text_input("Folder Name")
                add_folder = st.button("Create Folder", on_click=make_folder, args=[selected_folder, name])
                if add_folder:
                    print("Creating folder")
    st.write("Please select a channel and topic to view the videos.")
    if not st.session_state.channels:
        st.write("No channels found in database, attempt to pull from Telegram?")
        pull_ch_b = st.button("Pull Channels")
        if pull_ch_b:
            asyncio.run(pull_videos_from_tg())
            time.sleep(1)
            st.rerun()

    else:
        col1, col2 = st.columns(2)
        channel_list = [channel.ch_name for channel in st.session_state.channels]
        channel_select = col1.selectbox("Select a channel", channel_list)
        st.session_state.channel_select = [channel for channel in st.session_state.channels if channel.ch_name == channel_select][0]
        if st.session_state.topics is None:
            asyncio.run(get_topics_from_db())
        if not st.session_state.topics:
            st.write("No topics found in database, attempt to pull from Telegram?")
            pull_topics = col2.button("Pull Topics")
            st.write(f"Channel: {st.session_state.topics}")
            if pull_topics:
                asyncio.run(get_topics_from_tg())
                time.sleep(1)
                st.rerun()
        elif len(st.session_state.topics) > 0:
            st.write(f"Topics: {st.session_state.channel_select.ch_name}")
            topic_names = [topic.topic_name for topic in st.session_state.topics]
            topic_names = sorted(topic_names)
            topic_select = st.selectbox("Select a topic", topic_names)
            selected_topic = [topic for topic in st.session_state.topics if topic.topic_name == topic_select]
            st.session_state.topic_select = selected_topic
            st.write(f"Videos: {topic_select}")

    # if st.session_state.topics:
    #     print(st.session_state.topics)
    #     # topic_names = [topic[1] for topic in st.session_state.topics]
    #     # topic_select = col2.selectbox("Select a topic", topic_names)
    #     # st.session_state.topic_select = [topic for topic in st.session_state.topics if topic[1] == topic_select][0]
    #     topic = st.session_state.topics
    #     topic_names = [topic[1] for topic in st.session_state.topics]
    #     topic_names.sort()
    #     topic_select = st.selectbox("Select a topic", topic_names)
    #     st.session_state.topic_select = [topic for topic in st.session_state.topics if topic[1] == topic_select]
    # # if st.session_state.topic_select != topic_select or st.session_state.videos is None:
    # #     st.session_state.topic_select = [topic for topic in st.session_state.topics if topic[1] == topic_select]
    # #     st.session_state.videos = None
    #     st.write(f"Videos: {topic_select}")
    #
    # if st.session_state.videos is None:
    #     await get_videos()
    # if not st.session_state.videos:
    #     st.write("No videos found in database, attempt to pull from Telegram?")
    #     pull_videos = st.button("Pull Videos")
    #     if pull_videos:
    #         await pull_videos_from_tg()
    # col1, col2, col3  = st.columns(3)
    # refresh_videos = col1.button("Refresh Videos")
    # refresh_channels = col2.button("Refresh Channels")
    # refresh_topics = col3.button("Refresh Topics")
    # if refresh_videos:
    #     await pull_videos_from_tg()
    # if refresh_channels:
    #     await get_channels_from_tg()
    # if refresh_topics:
    #     await get_topics_from_tg()
    # if st.session_state.videos:
    #     st.write(f"Found {len(st.session_state.videos)} videos.")
    #     df = pd.DataFrame(st.session_state.videos)
    #     df['thumb'] = df['thumb'].apply(base64_to_image)
    #     # df['tags'] = df['id'].apply(get_tags)
    #     df.insert(0, "Select", False)
    #     df = st.data_editor(df,
    #                  hide_index=True,
    #                  use_container_width=True,
    #                       column_config={'thumb': st.column_config.ImageColumn(width='medium'),
    #                                      'Select': st.column_config.CheckboxColumn(required=True)
    #                                      }
    #                       )
    #     df.drop('Select', axis=1)
    #     selected = df[df['Select'] == True]
    #     selected_list = selected['name'].tolist()
    #     dl = st.button("Download Selected")
    #     # if dl:
    #     #     st.write("Downloading...")
    #     #     message_list = selected['msg_id'].tolist()
    #     #     cont = st.container(border=True)
    #     #     await download_videos(message_list)
    #
    # else:
    #     st.write("No videos found.")
    #     # st.write(st.session_state.videos)

if __name__ == '__main__':
    main()

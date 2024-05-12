import pandas as pd
from IPython.core.display import HTML

from utils import db_utils as db
import streamlit as st
import asyncio
import pandas as pd
from utils.data_utils import show_tags

if 'api_id' not in st.session_state:
    st.session_state.api_id = None
if 'api_hash' not in st.session_state:
    st.session_state.api_hash = None
if 'tg_obj' not in st.session_state:
    st.session_state.tg_obj = None
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

db_url = 'mysql+mysqlconnector://user:password@127.0.0.1:3306/moviesdb'
st.set_page_config(page_title="Telegram Video-Matic", page_icon=":tv:", layout="wide")


def how_to():
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


def set_apis(api_id, api_hash):
    st.session_state.api_id = api_id
    st.session_state.api_hash = api_hash


def api_entry():
    api_id = st.sidebar.text_input("API ID")
    api_hash = st.sidebar.text_input("API Hash")
    tok_len = True if len(api_id) == 8 and api_id.isdigit() else False
    hash_len = True if len(api_hash) == 32 and api_hash.isalpha() else False
    is_filled = True if not tok_len or not api_hash else False
    submit_apis = st.sidebar.button("Submit API",
                                    key="submit_apis",
                                    disabled=is_filled,
                                    on_click=set_apis,
                                    args=[api_id, api_hash])


def get_channels():
    query = 'SELECT * FROM tg_channel'
    st.session_state.channels = db.execute_db_command(db_url, query)


def get_topics():
    db_channel_id = st.session_state.channel_select[0]
    query = f"SELECT * FROM tg_topic WHERE telegram_channel_id='{db_channel_id}'"
    st.session_state.topics = db.execute_db_command(db_url, query)


def get_videos():
    topic = st.session_state.topic_select[0]
    query = f"SELECT * FROM tg_message WHERE topic_id='{topic[0]}'"
    st.session_state.videos = db.execute_db_command(db_url, query)


def base64_to_image(base64_str):
    """
    Converts a base64 string to an image.
    Args:
        base64_str:

    Returns:

    """
    # Decode base64 string to binary data
    return f'data:image/jpeg;base64,{base64_str}'


def get_tags(msg_id):
    return show_tags(db_url, msg_id)


async def main():
    st.title("Telegram Video-Matic")
    st.write("Welcome to the Telegram Video-Matic app.")
    st.write("Please select a channel and topic to view the videos.")
    if st.session_state.channels is None:
        get_channels()

    channel_names = [channel[1] for channel in st.session_state.channels]
    channel_select = st.selectbox("Select a channel", channel_names)
    st.session_state.channel_select = [channel for channel in st.session_state.channels if channel[1] == channel_select][0]
    if st.session_state.topics is None:
        get_topics()
    topic = st.session_state.topics
    topic_names = [topic[1] for topic in st.session_state.topics]
    topic_select = st.selectbox("Select a topic", topic_names)
    st.session_state.topic_select = [topic for topic in st.session_state.topics if topic[1] == topic_select]
    if st.session_state.topic_select != topic_select or st.session_state.videos is None:
        st.session_state.topic_select = [topic for topic in st.session_state.topics if topic[1] == topic_select]
        st.session_state.videos = None
    st.write(f"Videos: {topic_select}")
    if st.session_state.videos is None:
        get_videos()
    if st.session_state.videos:
        st.write(f"Found {len(st.session_state.videos)} videos.")
        df = pd.DataFrame(st.session_state.videos)
        df['thumb'] =  df['thumb'].apply(base64_to_image)
        df['tags'] = df['id'].apply(get_tags)
        df = st.dataframe(df,
                     hide_index=True,
                     use_container_width=True,
                          column_config={'thumb': st.column_config.ImageColumn()})



    else:
        st.write("No videos found.")
        # st.write(st.session_state.videos)

how_to()
api_entry()

if st.session_state.api_id and st.session_state.api_hash:
    asyncio.run(main())

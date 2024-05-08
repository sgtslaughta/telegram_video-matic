import pandas as pd

from utils.tg_utils import TGAccount
import streamlit as st
import asyncio
import pandas as pd

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


async def get_channels():
    st.session_state.channels = await st.session_state.tg_obj.get_channels()


async def get_topics(channel_name):
    st.session_state.topics = await st.session_state.tg_obj.get_topics(channel_name)


async def get_videos():
    channel = st.session_state.channel_select
    data = st.session_state.topics
    title_to_find = st.session_state.topic_select
    id_found = None
    for topic in data.values():
        if topic['title'] == title_to_find:
            id_found = topic['id']
            break
    if id_found:
        st.session_state.videos = \
            await st.session_state.tg_obj.get_videos_by_topic(channel, id_found)


async def main():
    st.title("Telegram Video-Matic")
    st.write("Welcome to the Telegram Video-Matic app.")
    if st.session_state.tg_obj is None:
        st.session_state.tg_obj = TGAccount(
            int(st.session_state.api_id),
            st.session_state.api_hash)
    if st.session_state.channels is None:
        await get_channels()
    channel_names = [channel['name'] for channel in st.session_state.channels.values()]
    channel_select = st.selectbox("Select a channel", channel_names)
    st.session_state.channel_select = channel_select
    if st.session_state.topics is None:
        await get_topics(channel_select)
    topic_names = [topic['title'] for topic in st.session_state.topics.values()]
    topic_select = st.selectbox("Select a topic", topic_names)
    if st.session_state.topic_select != topic_select or st.session_state.videos is None:
        st.session_state.topic_select = topic_select
        st.session_state.videos = None
    st.write(f"Videos: {topic_select}")
    if st.session_state.videos is None:
        await get_videos()
    if st.session_state.videos:
        df = pd.DataFrame(st.session_state.videos).transpose()
        st.dataframe(df)
        # st.write(st.session_state.videos)

how_to()
api_entry()

if st.session_state.api_id and st.session_state.api_hash:
    asyncio.run(main())

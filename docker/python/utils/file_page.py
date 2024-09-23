import streamlit as st
from .db_utils import DBHelper, MonitoredItem, Topic, DLFolder

if 'monitored_channels' not in st.session_state:
    st.session_state.monitored_channels = None

def get_monitored_channels():
    mon_chs = []
    dbh = DBHelper(st.session_state.db_url)


def draw_files_page(tab):
    tab.title('Files tab')
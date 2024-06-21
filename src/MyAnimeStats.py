import streamlit as st
from common.utils import set_page_config

set_page_config()

st.image("src/static/logo.png", width=300)

st.title("MyAnimeStats")

st.write("Welcome to MyAnimeStats!")

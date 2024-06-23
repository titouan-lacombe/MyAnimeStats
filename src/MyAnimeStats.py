import streamlit as st
from common.utils import set_page_config

set_page_config()

st.image("src/static/logo.png", width=300)

st.write("Welcome to MyAnimeStats!")

st.write("Here you will be able to analyse your MyAnimeList statistics and get insights on your watching habits.")

st.write("To get started, head to the [List Analysis](Analyse) page.")

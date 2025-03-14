import streamlit as st

from .filesystem import static


def set_page_config(**kwargs):
    st.set_page_config(
        page_title="MyAnimeStats", page_icon=str(static / "favicon.png"), **kwargs
    )

import httpx, pytz
import streamlit as st
from common.utils import set_page_config
from common.filesystem import anime_db_path
from common.user_list import UserList, UserNotFound
from common.franchises import get_user_franchises
from common.actions import get_user_animes, get_stats

set_page_config(
	layout="wide",
)

st.title("Analyse")

col1, col2, _ = st.columns([1, 1, 4])
user_name = st.session_state.get("user_name", "")
user_name = col1.text_input("MyAnimeList username", user_name)
st.session_state["user_name"] = user_name

# TODO get user timezone using js
timezones = list(sorted(pytz.all_timezones))
local_tz = col2.selectbox("Local timezone", timezones, index=timezones.index("UTC"))

@st.cache_data(show_spinner=False)
def analyse(user_name: str, local_tz: str):
	with httpx.Client() as client:
		user_list = UserList.from_user_name(client, user_name)
	user_animes = get_user_animes(user_list, anime_db_path)
	user_franchises = get_user_franchises(user_animes)
	stats = get_stats(user_animes, user_franchises, local_tz)
	return stats

if st.button("Analyse"):
	if not user_name:
		st.error("Please provide your MyAnimeList username")
		st.stop()

	with st.spinner("Analysing..."):
		try:
			stats = analyse(user_name, local_tz)
		except UserNotFound:
			st.error(f"User '{user_name}' not found")
			st.stop()
	
	st.write("## Favourite franchises")
	st.dataframe(stats["favorite_franchises"])

	# TODO: fix rendering
	# st.write("## Air schedule")
	# st.table(stats["air_schedule"])

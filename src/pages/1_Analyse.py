import httpx, pytz
import altair as alt
import streamlit as st
import polars as pl
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
	return stats, user_franchises, user_animes

if st.button("Analyse"):
	if not user_name:
		st.error("Please provide your MyAnimeList username")
		st.stop()

	with st.spinner("Analysing..."):
		try:
			stats, user_franchises, user_animes = analyse(user_name, local_tz)
		except UserNotFound:
			st.error(f"User '{user_name}' not found")
			st.stop()
	
	st.write("## Favourite franchises")
	st.dataframe(stats["favorite_franchises"])

	st.write(f"## Air schedule (in {local_tz})")
	st.dataframe(stats["air_schedule"])

	col1, col2 = st.columns(2)

	# TODO title_localized: title_english or title_japanese
	# # Histograms of 'score' and 'my_score'
	# user_animes.hvplot.kde(y=['scored_avg', 'user_scored'], alpha=0.5, title='Franchises Score Distribution', legend='top_right', height=500, width=800, xlim=(0, 10)) +
	col1.altair_chart(
		alt.Chart(
			user_animes.filter(pl.col('scored_avg').is_not_null() & pl.col('user_scored').is_not_null())
		).transform_fold(
			['scored_avg', 'user_scored'],
			as_=['variable', 'value']
		).transform_density(
			density='value',
			groupby=['variable'],
			as_=['value', 'density'],
			extent=[0, 10]
		).mark_area(opacity=0.5).encode(
			x=alt.X('value:Q', title='Score'),
			y=alt.Y('density:Q', title='Density'),
			color='variable:N'
		).properties(
			title='Franchises Score Distribution',
			width=800,
			height=500
		).interactive()
	)

	# # Average user score by air year
	# user_animes.hvplot.scatter(x='air_start', y='user_scored', title='User Score Distribution by Air Year', height=500, width=800, hover_cols=['title_english'])
	col2.altair_chart(
		alt.Chart(user_animes).mark_point().encode(
			x=alt.X('air_start:T', title='Air Year'),
			y=alt.Y('user_scored:Q', title='Score', scale=alt.Scale(domain=(0, 10))),
			tooltip=[
				alt.Tooltip('title_english:N', title='Title'),
				alt.Tooltip('user_scored:Q', title='Score'),
				alt.Tooltip('air_start:T', title='Air Start')
			]
		).properties(
			title='User Score Distribution by Air Year',
			width=800,
			height=500
		).interactive()
	)

	# def score_box_plot(key: str):
	# 	threshold = 8
	# 	box_data = user_animes.filter(
	# 		pl.col('user_scored').is_not_null()
	# 	).select("user_scored", key).explode(key).group_by(key).all().filter(
	# 		pl.col(key).is_not_null() & (pl.col('user_scored').list.len() >= threshold)
	# 	).cast({
	# 		# Removes filtered keys from the plot
	# 		key: pl.String
	# 	}).with_columns(
	# 		median_score=pl.col('user_scored').list.median()
	# 	).explode('user_scored').sort('median_score', key, descending=True)

	# 	return box_data.hvplot.box(
	# 		y='user_scored', by=key, title=f'User Score Distribution by {key.capitalize()}',
	# 		height=500, width=1200, rot=45, legend='top_right'
	# 	)

	# 	score_box_plot('genres'),
	# 	score_box_plot('themes'),
	# 	score_box_plot('studios'),
	# 	score_box_plot('demographics')
	def score_box_plot(key: str, col):
		threshold = 8
		box_data = user_animes.filter(
			pl.col('user_scored').is_not_null()
		).select("user_scored", key).explode(key).group_by(key).all().filter(
			pl.col(key).is_not_null() & (pl.col('user_scored').list.len() >= threshold)
		).cast({
			# Removes filtered keys from the plot
			key: pl.String
		}).with_columns(
			median_score=pl.col('user_scored').list.median()
		).explode('user_scored').sort('median_score', key, descending=True)

		col.altair_chart(
			alt.Chart(box_data).mark_boxplot().encode(
				x=alt.X(key, title=key.capitalize()),
				y=alt.Y('user_scored:Q', title='Score', scale=alt.Scale(domain=(0, 10))),
				tooltip=[
					alt.Tooltip(f'{key}:N', title=key.capitalize()),
					alt.Tooltip('user_scored:Q', title='Score')
				],
			).properties(
				title=f'User Score Distribution by {key.capitalize()}',
				width=800,
				height=500
			)
		)

	score_box_plot('genres', col1)
	score_box_plot('themes', col2)
	score_box_plot('studios', col1)
	score_box_plot('demographics', col2)

	# # Scale scores to remove bias in MAL users scoring and user scoring
	# def scale_scores(col: str):
	# 	"Scale scores to a range of 0 to 1 using rank scaling."
	# 	return pl.lit(1) - (pl.col(col).rank(descending=True) - 1) / (pl.col(col).count() - 1)

	# unpopular_data = user_animes.filter(
	# 	pl.col('scored_avg').is_not_null() & pl.col('user_scored').is_not_null()
	# ).with_columns(
	# 	user_scored_scaled = scale_scores('user_scored'),
	# 	scored_avg_scaled = scale_scores('scored_avg'),
	# ).with_columns(
	# 	score_difference = pl.col('user_scored_scaled') - pl.col('scored_avg_scaled')
	# ).with_columns(
	# 	score_difference_abs = pl.col('score_difference').abs()
	# ).sort("score_difference_abs", descending=True)

	# print_df(unpopular_data.select("title_english", "score_difference", "scored_avg", "user_scored").head(10), "Most unpopular opinions")
	def scale_scores(col: pl.Series) -> pl.Series:
		"Scale scores to a range of 0 to 1 using rank scaling."
		return 1 - (col.rank(descending=True) - 1) / (col.count() - 1)
	
	unpopular_data = user_animes.filter(
		pl.col('scored_avg').is_not_null() & pl.col('user_scored').is_not_null()
	).with_columns(
		user_scored_scaled = scale_scores(pl.col('user_scored')),
		scored_avg_scaled = scale_scores(pl.col('scored_avg')),
	).with_columns(
		score_difference = pl.col('user_scored_scaled') - pl.col('scored_avg_scaled')
	).with_columns(
		score_difference_abs = pl.col('score_difference').abs()
	).sort("score_difference_abs", descending=True)

	st.write("## Most unpopular opinions")

	col1, col2 = st.columns(2)
	col1.dataframe(unpopular_data.select("title_english", "score_difference", "scored_avg", "user_scored"))

	# normie_ness = 1 - (unpopular_data.get_column("score_difference_abs").mean() * 2)
	# print(f"[green]Normie-ness: {normie_ness:.2%}[/green]")
	normie_ness = 1 - (unpopular_data.get_column("score_difference_abs").mean() * 2)
	st.write(f"Normie-ness: {normie_ness:.2%}")

	# unpopular_data_colored = unpopular_data.with_columns(
	# 	color = pl.when(pl.col('score_difference_abs') <= 0.05)
	# 		.then(pl.lit('green'))
	# 		.when(pl.col('score_difference_abs') <= 0.15)
	# 		.then(pl.lit('orange'))
	# 		.otherwise(pl.lit('red'))
	# )

	# display(
	# 	unpopular_data_colored.hvplot.scatter(
	# 		x='scored_avg_scaled', y='user_scored_scaled', c='color', title='User Score vs MyAnimeList Score',
	# 		height=500, width=1200, grid=True,
	# 		hover_cols=['title_english']
	# 	)
	# 	* hv.Curve([(0, 0), (1, 1)], 'black', 'y=x')
	# )
	unpopular_data_colored = unpopular_data.with_columns(
		color = pl.when(pl.col('score_difference_abs') <= 0.05)
			.then(pl.lit('green'))
			.when(pl.col('score_difference_abs') <= 0.15)
			.then(pl.lit('orange'))
			.otherwise(pl.lit('red')
		)
	)

	col2.altair_chart(
		alt.Chart(unpopular_data_colored).mark_circle().encode(
			x=alt.X('scored_avg_scaled:Q', title='MyAnimeList Score'),
			y=alt.Y('user_scored_scaled:Q', title='User Score'),
			color=alt.Color('color:N', scale=None),
			tooltip=[
				alt.Tooltip('title_english:N', title='Title'),
				alt.Tooltip('scored_avg:Q', title='MyAnimeList Score'),
				alt.Tooltip('user_scored:Q', title='User Score'),
				alt.Tooltip('score_difference:Q', title='Normed Score Diff (%)')
			]
		).properties(
			title='User Score vs MyAnimeList Score',
			width=800,
			height=800
		).interactive()
	)

	# from itertools import combinations

	# def co_occurrence(data: pl.Series):
	# 	"Compute co-occurrence data from a list of lists."

	# 	co_occurrences = []
	# 	for row in data:
	# 		for feature1, feature2 in combinations(sorted(row), 2):
	# 			co_occurrences.append({
	# 				'feature1': feature1,
	# 				'feature2': feature2,
	# 			})

	# 	df = pl.DataFrame(
	# 		co_occurrences,
	# 	)

	# 	# Count co-occurrences
	# 	co_occurrence_counts = df.group_by(['feature1', 'feature2']).agg(
	# 		pl.len().alias('count')
	# 	).sort('count', descending=True)

	# 	return co_occurrence_counts

	# def draw_co_occurrence(feature: str):
	# 	"Draw a co-occurrence matrix with a title and masks the upper triangle."
	# 	occ_data = co_occurrence(user_animes.get_column(feature))
		
	# 	# TODO format data into a matrix with lower triangle masked
	# 	return occ_data.hvplot.heatmap(
	# 		x='feature1', y='feature2', C='count',
	# 		title=f"{feature.capitalize()} Co-occurrence Matrix",
	# 		width=800, height=800,
	# 		rot=45,
	# 	)

	# display(
	# 	draw_co_occurrence('genres'),
	# 	draw_co_occurrence('themes')
	# )
	from itertools import combinations
	def co_occurrence(data: pl.Series) -> pl.DataFrame:
		"Compute co-occurrence data from a list of lists."

		co_occurrences = []
		for row in data:
			for feature1, feature2 in combinations(sorted(row), 2):
				co_occurrences.append({
					'feature1': feature1,
					'feature2': feature2,
				})

		df = pl.DataFrame(
			co_occurrences,
		)

		# Count co-occurrences
		co_occurrence_counts = df.group_by(['feature1', 'feature2']).agg(
			pl.len().alias('count')
		).sort('count', descending=True)

		return co_occurrence_counts
	
	def draw_co_occurrence(feature: str, col):
		"Draw a co-occurrence matrix with a title and masks the upper triangle."
		occ_data = co_occurrence(user_animes.get_column(feature))
		
		# TODO format data into a matrix with lower triangle masked
		col.altair_chart(
			alt.Chart(occ_data).mark_rect().encode(
				x=alt.X('feature1:N', title='Feature 1'),
				y=alt.Y('feature2:N', title='Feature 2'),
				color=alt.Color('count:Q', title='Count'),
				tooltip=[
					alt.Tooltip('count:Q', title='Count'),
					alt.Tooltip('feature1:N', title='Feature 1'),
					alt.Tooltip('feature2:N', title='Feature 2')
				]
			).properties(
				title=f"{feature.capitalize()} Co-occurrence Matrix",
				width=800,
				height=800
			)
		)

	col1, col2 = st.columns(2)
	draw_co_occurrence('genres', col1)
	draw_co_occurrence('themes', col2)

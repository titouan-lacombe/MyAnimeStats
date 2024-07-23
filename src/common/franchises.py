import polars as pl

def first(col):
	return pl.col(col).first().alias(col)

def union(col):
	return pl.col(col).flatten().unique().alias(col)

def sum(col):
	return pl.col(col).sum().alias(col)

def weighted_mean(col, wh_col):
	return ((pl.col(col) * pl.col(wh_col)).sum() / pl.col(wh_col).sum()).fill_nan(None).alias(col)

def get_user_franchises(user_animes: pl.DataFrame):
	# Fake franchises
	user_animes = user_animes.with_columns(
		franchise = pl.col("title_localized"),
	)

	# Default franchise
	lazy_user_animes = user_animes.lazy().with_columns(
		pl.col("franchise").fill_null(pl.col("title_localized")),
	)

	# Calculate user_watch_duration and total_duration
	lazy_user_animes = lazy_user_animes.with_columns(
		user_watch_duration = pl.duration(
			seconds=pl.col("episode_avg_duration").dt.total_seconds() * pl.col("user_watch_episodes")
		).replace(0, None),
		total_duration = pl.duration(
			seconds=pl.col("episode_avg_duration").dt.total_seconds() * pl.col("episodes")
		).replace(0, None),
	)

	# TODO aggregate user_watch_status, user_watch_start, user_watch_end, air_start, air_end
	franchises = lazy_user_animes.group_by("franchise").agg(
		sum("episodes"),
		sum("user_watch_episodes"),
		weighted_mean("scored_avg", "episodes"),
		weighted_mean("user_scored", "episodes").replace(0, None),
		union("genres"),
		union("themes"),
		union("demographics"),
		union("studios"),
		union("licensors"),
		union("producers"),
		union("source"),
		union("rating"),
		union("type"),
		pl.col("sfw").all().alias("sfw"),
		pl.col("user_rewatching").any().alias("user_rewatching"),
		sum("user_watch_duration"),
		sum("total_duration"),
		pl.col("anime_id"),
	).sort("user_scored", descending=True, nulls_last=True)

	return franchises.collect()

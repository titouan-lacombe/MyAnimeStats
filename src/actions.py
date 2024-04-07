import logging
import polars as pl
from .schedule import Schedule
from .next_releases import NextReleases

logger = logging.getLogger(__name__)

def get_user_animes(user_list: pl.DataFrame):
	anime_db = pl.scan_parquet("data/anime.parquet")

	common_cols = set(user_list.columns).intersection(anime_db.columns).difference(["anime_id"])
	if len(common_cols) > 0:
		raise Exception(f"Common columns found between user_list and anime_db: {common_cols}")

	user_animes = user_list.lazy().join(anime_db, on="anime_id", how="inner", validate="1:1").collect()

	if user_animes.height < user_list.height:
		missing_animes = user_list.join(user_animes, "anime_id", "anti")
		logger.warning(f"{missing_animes.height} anime not found in database: {missing_animes.head(10)}")

	return user_animes

def get_stats(user_animes: pl.DataFrame):
	user_animes = user_animes.lazy()

	# Get all lazy stats
	schedule = Schedule.get(user_animes)
	next_releases = NextReleases.get(user_animes)

	# Collect all stats in parallel
	[schedule, next_releases] = pl.collect_all([schedule, next_releases])

	# Finish building the schedule
	schedule = Schedule.from_df(schedule)

	return schedule, next_releases

import logging
import polars as pl
from pathlib import Path
from .schedule import Schedule
from .next_releases import NextReleases

logger = logging.getLogger(__name__)

def get_user_animes(user_list: pl.DataFrame, anime_db_file: Path):
	anime_db = pl.scan_parquet(anime_db_file)

	common_cols = set(user_list.columns).intersection(anime_db.columns).difference(["anime_id"])
	if len(common_cols) > 0:
		raise Exception(f"Common columns found between user_list and anime_db: {common_cols}")

	user_animes = user_list.lazy().join(anime_db, on="anime_id", how="inner", validate="1:1").collect()

	if user_animes.height < user_list.height:
		missing_animes = user_list.join(user_animes, "anime_id", "anti")
		logger.warning(f"{missing_animes.height} anime not found in database: {missing_animes.head(10)}")

	return user_animes

def get_stats(user_animes: pl.DataFrame, user_tz: str):
	user_animes = user_animes.lazy()

	# Get all lazy stats
	lazy_stats = {
		"schedule": Schedule.get(user_animes),
		"next_releases": NextReleases.get(user_animes),
	}

	# Collect all stats in parallel
	stats_order = list(lazy_stats.keys())
	collected_stats = pl.collect_all([lazy_stats[stat] for stat in stats_order])
	stats = {name: collected for name, collected in zip(stats_order, collected_stats)}

	# Finish building the schedule
	stats["schedule"] = Schedule.from_df(stats["schedule"], user_tz)

	return stats

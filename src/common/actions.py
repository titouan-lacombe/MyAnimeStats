import logging
from datetime import datetime
from pathlib import Path

import polars as pl

from .next_releases import NextReleases
from .schedule import Schedule

logger = logging.getLogger(__name__)


def get_user_animes(user_list: pl.DataFrame, anime_db_file: Path):
    anime_db = pl.scan_parquet(anime_db_file).cast(
        {
            "anime_id": pl.UInt64,
        }
    )

    user_animes = (
        user_list.lazy()
        .join(anime_db, on="anime_id", how="inner", validate="1:1")
        .with_columns(
            # TODO better handling of localized titles
            title_localized=pl.col("title_english").fill_null(pl.col("title")),
        )
        .collect()
    )

    if user_animes.height < user_list.height:
        missing_animes = user_list.join(user_animes, "anime_id", "anti")
        logger.warning(
            f"{missing_animes.height} anime not found in database: {missing_animes.head(10)}"
        )

    return user_animes


def get_stats(
    user_animes: pl.DataFrame,
    user_franchises: pl.DataFrame,
    user_tz: str,
    now: datetime,
):
    user_animes = user_animes.lazy()
    user_franchises = user_franchises.lazy()

    # Get all lazy stats
    lazy_stats = {
        "favorite_franchises": user_franchises.sort(
            "user_scored", descending=True, nulls_last=True
        ),
        "air_schedule": Schedule.get(user_animes),
        "next_releases": NextReleases.get(user_animes, user_tz, now),
    }

    # Collect all stats in parallel
    stats_order = list(lazy_stats.keys())
    collected_stats = pl.collect_all([lazy_stats[stat] for stat in stats_order])
    stats = dict(zip(stats_order, collected_stats, strict=False))

    # Finish building the schedule
    stats["air_schedule"] = Schedule.from_df(stats["air_schedule"], user_tz)

    return stats

import logging
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

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
    user_time: datetime,
):
    default_tz = "Asia/Tokyo"

    def get_aware_dt(row: str):
        dt, tz = row.split("\t")
        return (
            datetime.fromisoformat(dt)
            .replace(tzinfo=ZoneInfo(tz))
            .astimezone(user_time.tzinfo)
        )

    user_animes = (
        user_animes.lazy()
        .with_columns(
            air_tz=pl.col("air_tz").fill_null(default_tz),
        )
        .with_columns(
            air_start_dt=(
                pl.col("air_start")
                .dt.combine(pl.col("air_time").replace(None, time(0, 0)))
                .dt.to_string()
                + "\t"
                + pl.col("air_tz")
            ).map_elements(
                get_aware_dt, return_dtype=pl.Datetime("us", str(user_time.tzinfo))
            )
        )
    )
    user_franchises = user_franchises.lazy()

    # Get all lazy stats
    lazy_stats = {
        "favorite_franchises": user_franchises.sort(
            "user_scored", descending=True, nulls_last=True
        ),
        "air_schedule": Schedule.get(user_animes, user_time),
        "next_releases": NextReleases.get(user_animes, user_time),
    }

    # Collect all stats in parallel
    stats_order = list(lazy_stats.keys())
    collected_stats = pl.collect_all([lazy_stats[stat] for stat in stats_order])
    stats = dict(zip(stats_order, collected_stats, strict=False))

    # Finish building the schedule
    stats["air_schedule"] = Schedule.from_df(stats["air_schedule"], user_time)

    return stats

import logging
from datetime import datetime
from pathlib import Path

import polars as pl

from .next_releases import NextReleases
from .schedule import Schedule

logger = logging.getLogger(__name__)


def get_user_animes(
    user_list: pl.DataFrame,
    anime_db_file: Path,
    user_langs: list[str],
):
    anime_db = pl.scan_parquet(anime_db_file).cast(
        {
            "anime_id": pl.UInt64,
        }
    )

    title_expr = pl.lit(None)
    for lang in user_langs:
        if "-" in lang:
            lang = lang.split("-")[0]

        lang_col = f"title_{lang}"
        if lang_col not in user_list.columns:
            logger.warning(f"Language {lang} not found in database")
            continue

        title_expr = title_expr.fill_null(pl.col(lang_col))

    title_expr = title_expr.fill_null(pl.col("title_default")).alias("title")

    user_animes = (
        user_list.lazy()
        .join(anime_db, on="anime_id", how="inner", validate="1:1")
        .with_columns(title_expr)
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
    user_animes_lazy = user_animes.lazy().with_columns(
        pl.col("air_start_dt").dt.convert_time_zone(str(user_time.tzinfo)),
        pl.col("air_end_dt").dt.convert_time_zone(str(user_time.tzinfo)),
    )
    user_franchises = user_franchises.lazy()

    # Get all lazy stats
    lazy_stats = {
        "favorite_franchises": user_franchises.sort(
            "user_scored", descending=True, nulls_last=True
        ),
        "air_schedule": Schedule.get(user_animes_lazy, user_time),
        "next_releases": NextReleases.get(user_animes_lazy, user_time),
    }

    # Collect all stats in parallel
    stats_order = list(lazy_stats.keys())
    collected_stats = pl.collect_all([lazy_stats[stat] for stat in stats_order])
    stats = dict(zip(stats_order, collected_stats, strict=False))

    # Finish building the schedule
    stats["air_schedule"] = Schedule.from_df(stats["air_schedule"], user_time)

    return stats

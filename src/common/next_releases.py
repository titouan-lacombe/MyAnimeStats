from datetime import datetime

import polars as pl

from .models import AirStatus, UserStatus


class NextReleases:
    @staticmethod
    def get(user_animes: pl.LazyFrame, user_time: datetime):
        # Patch since all animes are in JST (later we will use air_tz)
        return (
            user_animes.filter(
                (pl.col("user_watch_status") == UserStatus.PLAN_TO_WATCH)
                & (pl.col("air_status") == AirStatus.NOT_YET_AIRED)
                & (pl.col("air_start_dt").is_not_null())
                & (pl.col("air_start_dt") >= user_time)
            )
            .sort("air_start_dt")
            .with_columns(
                text=pl.col("air_start_dt").dt.to_string("%A %d %B %Y at %H:%M")
            )
            .select("title", "text")
            .rename(
                {
                    "title": "Title",
                    "text": "Air Date",
                }
            )
        )

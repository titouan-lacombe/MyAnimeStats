from datetime import datetime, time

import polars as pl

from .models import AirStatus, UserStatus


class NextReleases:
    @staticmethod
    def get(user_animes: pl.LazyFrame, user_time: datetime):
        # Patch since all animes are in JST (later we will use air_tz)
        animes_tz = "Asia/Tokyo"

        return (
            user_animes.filter(
                (pl.col("user_watch_status") == UserStatus.PLAN_TO_WATCH)
                & (pl.col("air_status") == AirStatus.NOT_YET_AIRED)
                & (pl.col("air_start").is_not_null())
                & (pl.col("air_start").dt.date() >= user_time.date())
            )
            .sort("air_start", nulls_last=True)
            .with_columns(
                text=pl.col("air_start")
                .dt.combine(pl.col("air_time").replace(None, time(0, 0)))
                .dt.replace_time_zone(animes_tz)
                .dt.convert_time_zone(str(user_time.tzinfo))
                .dt.to_string("%A %d %B %Y at %H:%M")
            )
            .select("title_localized", "text")
            .rename(
                {
                    "title_localized": "Title",
                    "text": "Air Date",
                }
            )
        )

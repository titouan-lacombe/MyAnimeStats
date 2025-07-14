import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import polars as pl

from .models import AirStatus, UserStatus

WEEK_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

logger = logging.getLogger(__name__)


class Schedule:
    @staticmethod
    def get(user_animes: pl.LazyFrame, user_time: datetime):
        next_week = user_time + timedelta(days=7)
        return user_animes.filter(
            (
                pl.col("user_watch_status").is_in(
                    [UserStatus.WATCHING, UserStatus.PLAN_TO_WATCH]
                )
            )
            & (
                pl.col("air_status").is_in(
                    [AirStatus.CURRENTLY_AIRING, AirStatus.NOT_YET_AIRED]
                )
            )
            & (pl.col("air_start_dt") < next_week)
        ).select(
            "title",
            "air_day",
            "air_time",
            "air_tz",
            "air_start_dt",
        )

    # Finish building the schedule with the user timezone
    @staticmethod
    def from_df(schedule_df: pl.DataFrame, user_time: datetime):
        # Sort the schedule by day and time
        start_of_week = user_time.date() - timedelta(days=user_time.weekday())

        # Build the schedule
        schedule = [[] for _ in range(len(WEEK_DAYS))]
        for row in schedule_df.rows(named=True):
            anime_air_day = row["air_day"]

            if anime_air_day is None:
                air_at: datetime = row["air_start_dt"]
            else:
                anime_air_day = WEEK_DAYS.index(anime_air_day)

                # Compute the next airing datetime
                air_at = datetime.combine(
                    start_of_week + timedelta(days=anime_air_day),
                    row["air_time"] or time(0, 0),
                    ZoneInfo(row["air_tz"]),
                )

                # Convert the datetime to user's timezone
                air_at = air_at.astimezone(user_time.tzinfo)

            schedule[air_at.date().weekday()].append(
                {"title": row["title"], "datetime": air_at}
            )

        # Sort the schedule by day and time
        schedule = [sorted(animes, key=lambda x: x["datetime"]) for animes in schedule]

        # Create a DataFrame with the schedule information
        max_len = max(len(animes) for animes in schedule)
        data = {day: [""] * max_len for day in WEEK_DAYS}

        for i, animes in enumerate(schedule):
            day = WEEK_DAYS[i]
            for j, anime in enumerate(animes):
                data[day][j] = (
                    f"{anime['datetime'].strftime('%H:%M')} - {anime['title']}"
                )

        return pl.DataFrame(data)

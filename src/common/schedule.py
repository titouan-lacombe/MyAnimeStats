import logging
from datetime import datetime, time, timedelta

import polars as pl
import pytz

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
    def get(user_animes: pl.LazyFrame):
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
            & (pl.col("air_day").is_not_null())
            & (pl.col("air_time").is_not_null())
        ).select(
            "title_localized",
            "air_day",
            "air_time",
            "air_tz",
        )

    def get_dt(week_day: str, time: time, from_tz_str: str, to_tz_str: str):
        "Get the datetime for the given week day and time in the user's timezone"

        to_tz = pytz.timezone(to_tz_str)
        from_tz = pytz.timezone(from_tz_str)

        # Get start of the week
        now = datetime.now(from_tz)
        start_of_week = now.date() - timedelta(days=now.weekday())

        # Get the day and time
        day_num = WEEK_DAYS.index(week_day)
        air_at = datetime.combine(start_of_week + timedelta(days=day_num), time)

        # Localize the datetime to the JST timezone
        air_at = from_tz.localize(air_at)

        # Normalize the datetime to handle daylight saving time transitions
        air_at = from_tz.normalize(air_at)

        # Convert the datetime to the local timezone
        return air_at.astimezone(to_tz)

    # Finish building the schedule with the user timezone
    def from_df(schedule_df: pl.DataFrame, user_tz: str):
        default_tz = "Asia/Tokyo"

        # Build the schedule from the filtered animes
        schedule = {day: [] for day in WEEK_DAYS}
        for row in schedule_df.rows(named=True):
            anime_tz = row["air_tz"]
            anime_air_day = row["air_day"]
            anime_air_time = row["air_time"]
            anime_tz = anime_tz if anime_tz is not None else default_tz

            if anime_tz is None or anime_air_time is None or anime_air_day is None:
                logger.warning(
                    f"Couldn't build schedule entry: missing infos for {row['title_localized']}"
                )
                continue

            dt: datetime = Schedule.get_dt(
                anime_air_day, anime_air_time, anime_tz, user_tz
            )
            air_day = dt.strftime("%A")
            schedule[air_day].append({"title": row["title_localized"], "datetime": dt})

        # Sort the schedule days by time of airing
        for animes in schedule.values():
            animes.sort(key=lambda x: x["datetime"])

        # Create a DataFrame with the schedule information
        max_len = max(len(animes) for animes in schedule.values())
        data = {day: [""] * max_len for day in WEEK_DAYS}

        for day, animes in schedule.items():
            for i, anime in enumerate(animes):
                data[day][i] = (
                    f"{anime['datetime'].strftime('%H:%M')} - {anime['title']}"
                )

        return pl.DataFrame(data)

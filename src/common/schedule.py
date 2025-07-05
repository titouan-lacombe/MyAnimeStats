import logging
from datetime import date, datetime, time, timedelta
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
            & (pl.col("air_day").is_not_null())
            & (pl.col("air_time").is_not_null())
            & (pl.col("air_start_dt") < next_week)
        ).select(
            "title_localized",
            "air_day",
            "air_time",
            "air_tz",
        )

    @staticmethod
    def get_dt(
        start_of_week: date,
        week_day: str,
        time: time,
        from_tz: ZoneInfo,
        to_tz: ZoneInfo,
    ):
        "Get the datetime for the given week day and time in the user's timezone"

        # Get the day and time
        day_num = WEEK_DAYS.index(week_day)
        air_at = datetime.combine(
            start_of_week + timedelta(days=day_num),
            time,
            from_tz,
        )

        # Convert the datetime to the local timezone
        return air_at.astimezone(to_tz)

    # Finish building the schedule with the user timezone
    @staticmethod
    def from_df(schedule_df: pl.DataFrame, user_time: datetime):
        # Sort the schedule by day and time
        start_of_week = user_time.date() - timedelta(days=user_time.weekday())

        # Build the schedule
        schedule = {day: [] for day in WEEK_DAYS}
        for row in schedule_df.rows(named=True):
            anime_tz = ZoneInfo(row["air_tz"])
            anime_air_day = row["air_day"]
            anime_air_time = row["air_time"]

            # TODO id air day is null, use air_start.date().weekday()

            if anime_tz is None or anime_air_time is None or anime_air_day is None:
                logger.warning(
                    f"Couldn't build schedule entry: missing infos for {row['title_localized']}"
                )
                continue

            dt: datetime = Schedule.get_dt(
                start_of_week,
                anime_air_day,
                anime_air_time,
                anime_tz,
                user_time.tzinfo,
            )
            air_day = dt.strftime("%A")
            schedule[air_day].append({"title": row["title_localized"], "datetime": dt})

        # Sort the schedule by day and time
        for day in WEEK_DAYS:
            schedule[day] = sorted(schedule[day], key=lambda x: x["datetime"])

        # Create a DataFrame with the schedule information
        max_len = max(len(animes) for animes in schedule.values())
        data = {day: [""] * max_len for day in WEEK_DAYS}

        for day, animes in schedule.items():
            for i, anime in enumerate(animes):
                data[day][i] = (
                    f"{anime['datetime'].strftime('%H:%M')} - {anime['title']}"
                )

        return pl.DataFrame(data)

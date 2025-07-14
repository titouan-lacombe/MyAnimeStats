import logging
from io import TextIOWrapper

import httpx
import polars as pl

from .models import UserPriority, UserStatus

logger = logging.getLogger(__name__)

STATUS_MAP = {
    1: UserStatus.WATCHING,
    2: UserStatus.COMPLETED,
    3: UserStatus.ON_HOLD,
    4: UserStatus.DROPPED,
    6: UserStatus.PLAN_TO_WATCH,
}

USER_LIST_SCHEMA = {
    "anime_id": pl.UInt64,
    "status": pl.UInt8,
    "score": pl.UInt8,
    "is_rewatching": pl.Boolean,
    "num_watched_episodes": pl.UInt16,
    "is_added_to_list": pl.Boolean,
    "start_date_string": pl.String,
    "finish_date_string": pl.String,
    "days_string": pl.String,
    "storage_string": pl.String,
    "priority_string": pl.String,
    "notes": pl.String,
    "editable_notes": pl.String,
    "tags": pl.String,
}


class UserNotFoundError(Exception):
    pass


class UserList:
    @staticmethod
    def clean(df: pl.LazyFrame):
        # Cast to the correct types & select only the necessary columns
        df = df.select(USER_LIST_SCHEMA.keys()).cast(USER_LIST_SCHEMA)

        # Rename columns to avoid conflicts with other tables & prettier
        df = df.rename(
            {
                "score": "user_scored",
                "status": "user_watch_status",
                "start_date_string": "user_watch_start",
                "finish_date_string": "user_watch_end",
                "num_watched_episodes": "user_watch_episodes",
                "is_rewatching": "user_rewatching",
                "priority_string": "user_priority",
                "storage_string": "user_storage",
                "is_added_to_list": "user_added_to_list",
                "notes": "user_notes",
                "editable_notes": "user_editable_notes",
                "tags": "user_tags",
            }
        )

        # Drop redundant columns
        df = df.drop("days_string")

        # Set some columns to null if they're empty
        df = df.with_columns(
            [
                pl.col(col).replace("", None)
                for col in [
                    "user_storage",
                    "user_priority",
                    "user_notes",
                    "user_editable_notes",
                    "user_tags",
                ]
            ]
        )

        # Score 0 means no score
        df = df.with_columns(
            user_scored=pl.col("user_scored").replace(0, None),
        )

        # Convert status & priority to enums
        df = df.with_columns(
            user_watch_status=pl.col("user_watch_status")
            .replace_strict(STATUS_MAP, return_dtype=pl.String)
            .cast(pl.Enum(STATUS_MAP.values())),
            user_priority=pl.col("user_priority").cast(
                pl.Enum([UserPriority.LOW, UserPriority.MEDIUM, UserPriority.HIGH])
            ),
        )

        # Parse dates
        return df.with_columns(
            [
                pl.col(col).str.to_date(strict=False)
                for col in ["user_watch_start", "user_watch_end"]
            ]
        )

    @staticmethod
    def from_user_name(http_client: httpx.Client, user: str):
        "Scrapes the user's anime list from the web"

        # Hardcoded but no choice
        mal_chunk_size = 300

        total_entries = 0
        df = pl.DataFrame(
            schema=USER_LIST_SCHEMA,
        )

        while True:
            logger.info(f"Scraping web list with offset {total_entries}...")

            response = http_client.get(
                f"https://myanimelist.net/animelist/{user}/load.json",
                params={
                    "offset": total_entries,
                    "status": 7,  # All statuses
                },
                timeout=httpx.Timeout(
                    connect=10,
                    pool=10,
                    write=10,
                    read=10,
                ),
            )
            if response.status_code == 400:
                raise UserNotFoundError
            response.raise_for_status()
            entries = response.json()

            # Increment the offset
            new_entries = len(entries)
            total_entries += new_entries

            # Append the new entries to the dataframe
            df = df.vstack(
                pl.DataFrame(
                    entries,
                    schema=USER_LIST_SCHEMA,
                ),
            )

            # Check if we're done
            if new_entries < mal_chunk_size:
                logger.info(
                    f"Finished scraping user web list ({total_entries} total entries)"
                )
                break

        return UserList.clean(df.rechunk().lazy()).collect()

    @staticmethod
    def from_xml(file: TextIOWrapper) -> pl.DataFrame:
        "Loads the user's anime list from a MAL XML export file"
        # TODO: Implement from_xml
        raise NotImplementedError

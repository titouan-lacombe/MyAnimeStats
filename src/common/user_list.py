import logging, httpx
import polars as pl
from io import TextIOWrapper

logger = logging.getLogger(__name__)

STATUS_MAP = {
	1: "Watching",
	2: "Completed",
	3: "On-Hold",
	4: "Dropped",
	6: "Plan to Watch",
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

class UserNotFound(Exception):
	pass

class UserList:
	def clean(df: pl.LazyFrame) -> pl.LazyFrame:
		# Cast to the correct types & select only the necessary columns
		df = df.select(USER_LIST_SCHEMA.keys()).cast(USER_LIST_SCHEMA)

		# Rename columns to avoid conflicts with other tables & prettier
		df = df.rename({
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
		})

		# Drop redundant columns
		df = df.drop("days_string")

		# Set some columns to null if they're empty
		df = df.with_columns([
			pl.col(col).replace("", None)
			for col in ["user_storage", "user_priority", "user_notes", "user_editable_notes", "user_tags"]
		])

		# Score 0 means no score
		df = df.with_columns(
			user_scored = pl.col("user_scored").replace(0, None),
		)

		# Convert status & priority to enums
		df = df.with_columns(
			user_watch_status = pl.col("user_watch_status").replace(STATUS_MAP).cast(pl.Enum(STATUS_MAP.values())),
			user_priority = pl.col("user_priority").cast(pl.Enum(["Low", "Medium", "High"])),
		)

		# Parse dates
		df = df.with_columns([
			pl.col(col).str.to_date(strict=False)
			for col in ["user_watch_start", "user_watch_end"]
		])

		return df

	def from_user_name(http_client: httpx.Client, user: str):
		"Scrapes the user's anime list from the web"

		# Hardcoded but no choice
		mal_chunk_size = 300

		total_entries = 0
		df = pl.DataFrame()

		while True:
			logger.info(f"Scraping web list with offset {total_entries}...")

			response = http_client.get(f"https://myanimelist.net/animelist/{user}/load.json", params={
				"offset": total_entries,
				'status': 7, # All statuses
			})
			if response.status_code == 400:
				raise UserNotFound
			response.raise_for_status()
			entries = response.json()

			# Increment the offset
			new_entries = len(entries)
			total_entries += new_entries

			# Append the new entries to the dataframe
			df = df.vstack(pl.DataFrame(entries))

			# Check if we're done
			if new_entries < mal_chunk_size:
				logger.info(f"Finished scraping user web list ({total_entries} total entries)")
				break

		df.rechunk()
		cleaned: pl.DataFrame = UserList.clean(df.lazy()).collect()
		return cleaned

	def from_xml(file: TextIOWrapper) -> pl.DataFrame:
		"Loads the user's anime list from a MAL XML export file"
		# TODO: Implement from_xml
		raise NotImplementedError

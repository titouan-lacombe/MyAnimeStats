import httpx
import polars as pl
from src.log import logger

log = logger.getChild(__name__)

STATUS_MAP = {
	1: "Watching",
	2: "Completed",
	3: "On-Hold",
	4: "Dropped",
	6: "Plan to Watch",
}

USER_LIST_SCHEMA = {
	"anime_id": pl.Int64,
	"status": pl.Int8,
	"score": pl.Int8,
	"is_rewatching": pl.Boolean,
	"num_watched_episodes": pl.Int16,
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

class UserList:
	def __init__(self, df: pl.LazyFrame):
		self.df = df

	def clean(self):
		# Cast to the correct types & select only the necessary columns
		self.df = self.df.select(USER_LIST_SCHEMA.keys()).cast(USER_LIST_SCHEMA)

		# Rename columns to avoid conflicts with other tables & prettier
		self.df = self.df.rename({
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
		self.df = self.df.drop("days_string")

		# Set some columns to null if they're empty
		self.df = self.df.with_columns([
			pl.col(col).replace("", None)
			for col in ["user_storage", "user_priority", "user_notes", "user_editable_notes", "user_tags"]
		])

		# Score 0 means no score
		self.df = self.df.with_columns(
			user_scored = pl.col("user_scored").replace(0, None),
		)

		# Convert status & priority to enums
		self.df = self.df.with_columns(
			user_watch_status = pl.col("user_watch_status").replace(STATUS_MAP).cast(pl.Enum(STATUS_MAP.values())),
			user_priority = pl.col("user_priority").cast(pl.Enum(["Low", "Medium", "High"])),
		)

		# Parse dates
		self.df = self.df.with_columns([
			pl.col(col).str.to_date("%d-%m-%y")
			for col in ["user_watch_start", "user_watch_end"]
		])

		return self.df

	async def from_web(user, http_client: httpx.AsyncClient):
		"Scrapes the user's anime list from the web"

		start_offset = 0

		df = pl.DataFrame()
		while True:
			log.info(f"Scraping user web list with offset {start_offset}...")
			response = await http_client.get(f"https://myanimelist.net/animelist/{user}/load.json", params={
				"offset": start_offset,
				'status': 7,
			})
			response.raise_for_status()
			entries = response.json()

			# Increment the offset
			data_length = len(entries)
			start_offset += data_length

			# Check if we're done
			if data_length == 0:
				log.info(f"Finished scraping user web list ({start_offset} total entries)")
				break

			df = pl.DataFrame(entries)
			df = df.vstack(df)

		df.rechunk()
		user_list = UserList(df)
		user_list.clean()

		return user_list

	def from_xml(file):
		"Loads the user's anime list from a MAL XML export file"
		# TODO: Implement from_xml
		raise NotImplementedError

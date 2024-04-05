import httpx
import polars as pl
from src.log import logger

log = logger.getChild(__name__)

USER_LIST_SCHEMA = {
	"anime_id": pl.Int64,
	"status": pl.Int64,
	"score": pl.Int64,
	"is_rewatching": pl.Int64,
	"num_watched_episodes": pl.Int64,
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
	async def from_web(user, http_client: httpx.AsyncClient):
		"Scrapes the user's anime list from the web"

		start_offset = 0

		user_list = pl.DataFrame()
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
			df = df.select(USER_LIST_SCHEMA.keys()).cast(USER_LIST_SCHEMA)
			user_list = user_list.vstack(df)

		user_list = user_list.rename({
			"score": "user_score",
			"status": "user_status",
		})

		return user_list.rechunk()

	def from_xml(file):
		"Loads the user's anime list from a MAL XML export file"
		# TODO: Implement from_xml
		raise NotImplementedError

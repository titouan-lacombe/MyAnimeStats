import json, time, copy
from tqdm import tqdm
from jikanpy import AioJikan
from pathlib import Path

jikan_sleep_time = 1.1

data = Path('data')
cache = data / '.cache'

# MAL data
anime_key_map = {
	'my_watched_episodes': int,
	'my_start_date': None,
	'my_finish_date': None,
	'my_rated': None,
	'my_score': int,
	'my_storage': None,
	'my_storage_value': None,
	'my_status': None,
	'my_comments': None,
	'my_times_watched': int,
	'my_rewatch_value': None,
	'my_priority': None,
	'my_tags': None,
	'my_rewatching': int,
	'my_rewatching_ep': int,
	'my_discuss': int,
	'my_sns': None,
}

# Jikan API data
details_key_map = {
	'mal_id': int,
	'url': None,
	'images': None,
	'trailer': None,
	'approved': None,
	'title': None,
	'title_english': None,
	'title_japanese': None,
	'title_synonyms': None,
	'type': None,
	'source': None,
	'episodes': None,
	'status': None,
	'airing': None,
	'aired': None,
	'duration': None,
	'rating': None,
	'score': None,
	'scored_by': None,
	'rank': None,
	'popularity': None,
	'members': None,
	'favorites': None,
	'synopsis': None,
	'background': None,
	'season': None,
	'year': None,
	'broadcast': None,
	'producers': None,
	'licensors': None,
	'studios': None,
	'genres': None,
	'explicit_genres': None,
	'themes': None,
	'demographics': None,
}

def clean_fields(data: dict, fields: dict):
	for field in list(data.keys()):  # Iterate over a copy of the keys
		if field not in fields:
			del data[field]
		elif isinstance(data[field], dict) and isinstance(fields[field], dict):
			clean_fields(data[field], fields[field])
		elif fields[field] is not None and data[field] is not None:
			data[field] = fields[field](data[field])

# Complete anime entry with data from Jikan API
def complete_anime(anime: dict, details: dict):
	# Define key map for necessary fields and their corresponding types
	details_copy = copy.deepcopy(details)
	clean_fields(details_copy, details_key_map)
	anime_copy = copy.deepcopy(anime)
	clean_fields(anime_copy, anime_key_map)

	# Create complete anime object
	complete_anime = {**details_copy, **anime_copy}

	# Minimum one episode
	if complete_anime['episodes'] is None:
		complete_anime['episodes'] = 1

	return complete_anime

async def fetch_and_complete_anime(anime: dict, aio_jikan: AioJikan):
	anime_id = int(anime['series_animedb_id'])
	# print(f"Fetching details for {anime['series_title']} ({anime_id})")
	
	cache_file = cache / "anime" / f"{anime_id}.json"
	if cache_file.exists():
		# print("Using cached data")
		response = json.load(cache_file.open())
		return complete_anime(anime, response["data"])

	# print("Fetching data")
	response = await aio_jikan.anime(anime_id)
	complete = complete_anime(anime, response["data"])
	time.sleep(jikan_sleep_time)  # Sleep to avoid rate limiting

	# If anime finished airing, cache the data
	if complete['status'] == 'Finished Airing':
		# print("Caching data")
		cache_file.parent.mkdir(parents=True, exist_ok=True)
		json.dump(response, cache_file.open('w'))
	
	return complete

# Complete the animelist with data from Jikan API
async def complete_animes(animes: list, aio_jikan: AioJikan):
	completed = []
	for anime in tqdm(animes):
		result = await fetch_and_complete_anime(anime, aio_jikan)
		completed.append(result)

	return completed

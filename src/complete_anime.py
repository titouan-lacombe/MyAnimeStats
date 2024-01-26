import copy
from tqdm import tqdm
from datetime import datetime

from .cache import anime_cache

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

def parse_field(data: dict, field: str, parser):
	fields = field.split(".")

	while len(fields) > 1:
		data = data[fields.pop(0)]
	
	field = fields.pop(0)
	if data[field] is None:
		return
	data[field] = parser(data[field])

# Complete anime entry with data from Jikan API
def complete_anime(anime: dict, details: dict):
	# Define key map for necessary fields and their corresponding types
	details_copy = copy.deepcopy(details)
	clean_fields(details_copy, details_key_map)
	anime_copy = copy.deepcopy(anime)
	clean_fields(anime_copy, anime_key_map)

	# Create complete anime object
	complete_anime = {**details_copy, **anime_copy}

	# Parse some fields
	parse_field(complete_anime, "aired.from", lambda date: datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z'))
	parse_field(complete_anime, "aired.to", lambda date: datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z'))

	# Minimum one episode
	if complete_anime['episodes'] is None:
		complete_anime['episodes'] = 1

	return complete_anime

# Complete the animelist with data from Jikan API
async def complete_animes(animes: list):
	completed = []
	for anime in tqdm(animes):
		response = await anime_cache.get(id=int(anime['series_animedb_id']))
		completed.append(complete_anime(anime, response))

	return completed

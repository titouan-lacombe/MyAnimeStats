import aiohttp, xmltodict, gzip
from dicttoxml2 import dicttoxml

# Scrape the user's anime list from the web
async def scrape_animelist(user, aiohttp: aiohttp.ClientSession):
	# Get the user's anime list
	url = f"https://myanimelist.net/animelist/{user}/load.json?status=7"
	start_offset = 0

	results = []
	while True:
		# Get the data
		print(f"Scraping web list with offset {start_offset}...")
		async with aiohttp.get(f"{url}&offset={start_offset}") as response:
			entries = await response.json()
		results.extend(entries)

		# Increment the offset
		data_length = len(entries)
		start_offset += data_length

		# Check if we're done
		if data_length == 0:
			print(f"Scraped {start_offset} entries, done!")
			break

	return results

# Convert the web scrapped data to the MAL XML export format
def convert_to_exported_format(scrapped_data):
	# Initialize the result with some default values
	result = {
	}

	conversion_map = {
		'anime_id': 'series_animedb_id',
		'anime_title': 'series_title',
		'anime_num_episodes': 'series_episodes',
		'anime_media_type_string': 'series_type',
		'score': 'my_score',
		'notes': 'my_comments',
		'num_watched_episodes': 'my_watched_episodes',
		'finish_date_string': 'my_finish_date',
		'start_date_string': 'my_start_date',
		'tags': 'my_tags',
		'is_rewatching': 'my_rewatching',
		'storage_string': 'my_storage',
		'priority_string': 'my_priority',
		'status': 'my_status',
	}

	# Convert the data using the map
	for key_scrapped, key_export in conversion_map.items():
		result[key_export] = scrapped_data.get(key_scrapped, None)

	status_map = {
		1: 'Watching',
		2: 'Completed',
		3: 'On Hold',
		4: 'Dropped',
		6: 'Plan to Watch',
	}

	# Convert the status
	result['my_status'] = status_map.get(result['my_status'], None)

	return result

# Save an animelist to the same format as the MAL XML export
def save_animelist(animelist, file):
	xml = dicttoxml(
		{'anime': animelist},
		custom_root='myanimelist',
		attr_type=False,
		cdata=True,
		fold_list=False,
	)

	with gzip.open(file, 'w') as f:
		f.write(xml)

# Load the animelist from the web
async def load_web_list(user, aiohttp):
	# Scrapes the anime list of the user
	animelist = await scrape_animelist(user, aiohttp)

	# Convert to MyAnimeList XML export format
	animelist = [convert_to_exported_format(data) for data in animelist]

	# Return
	return animelist

# Load the animelist from a MAL XML export file
def load_xml_list(file):
	with gzip.open(file, 'rb') as f:
		return xmltodict.parse(f)['myanimelist']['anime']

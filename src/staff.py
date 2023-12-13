import json, time
from datetime import datetime
from tqdm import tqdm
from jikanpy import AioJikan
from pathlib import Path

data = Path('data')
cache = data / '.cache'

async def fetch_staff(anime, jikan: AioJikan):
	anime_id = anime['mal_id']

	cache_file = cache / "anime_staff" / f"{anime_id}.json"
	if cache_file.exists():
		# print("Using cached data")
		response = json.load(cache_file.open())
		return response

	response = await jikan.anime(anime_id, extension='staff')
	time.sleep(1.1)  # Sleep to avoid rate limiting
	
	# If anime finished airing, cache the data
	if anime['status'] == 'Finished Airing':
		# print("Caching data")
		cache_file.parent.mkdir(parents=True, exist_ok=True)
		json.dump(response, cache_file.open('w'))

	return response

async def fetch_characters(anime, jikan: AioJikan):
	anime_id = anime['mal_id']

	cached = cache / "anime_characters" / f"{anime_id}.json"
	if cached.exists():
		# print("Using cached data")
		response = json.load(cached.open())
		return response
	
	response = await jikan.anime(anime_id, extension='characters')
	time.sleep(1.1)  # Sleep to avoid rate limiting

	# If anime finished airing, cache the data
	if anime['status'] == 'Finished Airing':
		# print("Caching data")
		cached.parent.mkdir(parents=True, exist_ok=True)
		json.dump(response, cached.open('w'))

	return response

# Recover all people that worked on watched animes
async def get_staff(animes, aio_jikan, score_min=0):
	# Filter animes by status and score
	animes = {anime["mal_id"]: anime for anime in animes if anime["my_status"] != "Plan to Watch" and anime["my_score"] >= score_min}

	peoples = {}

	def add_people(people, anime_id, positions):
		if people['mal_id'] not in peoples:
			peoples[people['mal_id']] = people
			peoples[people['mal_id']]['animes'] = {}

		animes = peoples[people['mal_id']]['animes']
		if anime_id not in animes:
			animes[anime_id] = []
		
		animes[anime_id].extend(positions)

	for anime in tqdm(animes.values()):
		staff = await fetch_staff(anime, aio_jikan)
		for staff_member in staff['data']:
			# TODO position blacklist?
			add_people(staff_member['person'], anime['mal_id'], staff_member['positions'])

		characters = await fetch_characters(anime, aio_jikan)
		for character in characters['data']:
			for voice_actor in character['voice_actors']:
				if voice_actor['language'] != 'Japanese':
					continue
				add_people(voice_actor['person'], anime['mal_id'], [f"{character['character']['name']} VA"])

	print(f"Found {len(peoples)} people")

	return peoples

def print_staff(peoples, animes):
	# Create indexed animes list
	animes = {anime["mal_id"]: anime for anime in animes}

	# Only display people with more than X works
	peoples_list = [people for people in peoples.values() if len(people['animes']) > 1]

	# Sort people by number of works
	peoples_list.sort(key=lambda people: len(people['animes']), reverse=True)

	# Only show top 10 people
	for people in peoples_list[:10]:
		works = [{
			"anime": animes[anime_id],
			"positions": positions
		} for anime_id, positions in people['animes'].items()]

		# Sort works by anime airing date (to reflect artist evolution)
		works.sort(key=lambda work: work["anime"]["aired"]["from"])

		# TODO Don't show following works if same VA on same character?
		# TODO add link to show work (f"https://www.youtube.com/results?search_query={people['name']}")
		print(f"\n{people['name']} ({len(works)} works):")
		for work in works:
			date = datetime.strptime(work["anime"]["aired"]["from"], '%Y-%m-%dT%H:%M:%S%z')
			anime = work["anime"]
			anime_title = anime['title_english'] or anime['title']
			print(f"[{date.year}] {anime_title}: {', '.join(work["positions"])}")

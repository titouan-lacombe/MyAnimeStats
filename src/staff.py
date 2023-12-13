from datetime import datetime
from tqdm import tqdm

from .cache import staff_cache, character_cache

position_blacklist = []

# Recover all people that worked on watched animes
async def get_staff(animes, score_min=0):
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
		staff = await staff_cache.get(anime=anime)
 
		for staff_member in staff:
			positions = [position for position in staff_member['positions'] if position not in position_blacklist]
			add_people(staff_member['person'], anime['mal_id'], positions)

		characters = await character_cache.get(anime=anime)
		for character in characters:
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
		showreel_url = f"https://www.youtube.com/results?search_query={people['name']}"
		print(f"\n{people['name']} ({len(works)} works) - {showreel_url}")
		for work in works:
			date = datetime.strptime(work["anime"]["aired"]["from"], '%Y-%m-%dT%H:%M:%S%z')
			anime = work["anime"]
			anime_title = anime['title_english'] or anime['title']
			print(f"[{date.year}] {anime_title}: {', '.join(work["positions"])}")

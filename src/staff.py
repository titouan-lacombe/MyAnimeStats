from urllib.parse import quote
from tqdm import tqdm

from .cache import staff_cache, character_cache
from .log import logger

log = logger.getChild(__name__)

# Recover all person that worked on watched animes
async def get_staff(animes, score_min=0, position_blacklist=[]):
	# Filter animes by status and score
	def filter_anime(anime):
		return anime["my_status"] != "Plan to Watch" and anime["my_score"] >= score_min
	animes = [anime for anime in animes if filter_anime(anime)]

	persons = {}
	def register_person(person):
		id = person['mal_id']
		if id in persons:
			return persons[id]
		persons[id] = person
		person['animes'] = {}
		person['characters'] = {}
		return person

	def add_positions(person, anime, positions):
		person = register_person(person)
		person['animes'][anime['mal_id']] = {
			"anime": anime,
			"positions": positions
		}

	def add_character(person, anime, character):
		person = register_person(person)
		if character['mal_id'] in person['characters']:
			person['characters'][character['mal_id']]['animes'].append(anime)
			return
		person['characters'][character['mal_id']] = {
			"animes": [anime],
			"character": character
		}

	for anime in tqdm(animes):
		staff = await staff_cache.get(anime=anime)
		for staff_member in staff:
			positions = [position for position in staff_member['positions'] if position not in position_blacklist]
			add_positions(staff_member['person'], anime, positions)

		characters = await character_cache.get(anime=anime)
		for character in characters:
			for voice_actor in character['voice_actors']:
				if voice_actor['language'] != 'Japanese':
					continue
				add_character(voice_actor['person'], anime, character['character'])

	# Convert dict to list and sort
	persons = list(persons.values())
	for person in persons:
		# Sort anime by airing date (to reflect artist evolution)
		person['animes'] = list(person['animes'].values())
		person['animes'].sort(key=lambda anime: anime['anime']['aired']['from'])

		# Sort characters by anime airing date (to reflect artist evolution)
		person['characters'] = list(person['characters'].values())
		for character in person['characters']:
			character['animes'].sort(key=lambda anime: anime['aired']['from'])
		person['characters'].sort(key=lambda character: character['animes'][0]['aired']['from'])
		
		person['works'] = len(person['animes']) + len(person['characters'])

	log.info(f"Found {len(persons)} persons")

	# Sort person by number of works
	persons.sort(key=lambda person: person['works'], reverse=True)

	return persons

def print_staff(persons, show_top=10, min_works=2):
	# Only display person with more than X works
	persons = [person for person in persons if len(person['animes']) + len(person['characters']) >= min_works]

	for person in persons[:show_top]:
		showreel_url = f"https://www.youtube.com/results?search_query={quote(person['name'])}"
		print(f"\n{person['name']} ({person['works']} works) - {showreel_url}")

		if len(person['animes']) > 0:
			print("Anime staff:")
		for work in person['animes']:
			anime = work["anime"]
			anime_title = anime['title_english'] or anime['title']
			print(f"[{anime['aired']['from'].year}] {', '.join(work['positions'])} ({anime_title})")

		if len(person['characters']) > 0:
			print("Character voice actor:")
		for work in person['characters']:
			character = work["character"]
			animes = work["animes"]
			animes_title = ', '.join([anime['title_english'] if anime['title_english'] is not None else anime['title'] for anime in animes])
			print(f"[{animes[0]['aired']['from'].year}] {character['name']} ({animes_title})")
	
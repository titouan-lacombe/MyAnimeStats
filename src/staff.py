from urllib.parse import quote
from tqdm import tqdm

from .cache import staff_cache, character_cache
from .log import logger

log = logger.getChild(__name__)

default_position_blacklist = [
    "ADR Director", # Doesn't matter if watching in Japanese
    "Producer",
    "Executive Producer",
    "Planning",
]

default_language_whitelist = [
    "Japanese", # Japanese voice actors
]

# Recover all person that worked on watched animes
async def get_staff(animes, score_min=8, position_blacklist=None, language_whitelist=None):
    if position_blacklist is None:
        position_blacklist = default_position_blacklist

    if language_whitelist is None:
        language_whitelist = default_language_whitelist

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

    def add_position(person, anime, position):
        person = register_person(person)
        if anime['mal_id'] in person['animes']:
            person['animes'][anime['mal_id']]['positions'].append(position)
            return
        person['animes'][anime['mal_id']] = {
            "anime": anime,
            "positions": [position]
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
            for position in staff_member['positions']:
                if position in position_blacklist:
                    continue
                add_position(staff_member['person'], anime, position)

        characters = await character_cache.get(anime=anime)
        for character in characters:
            for voice_actor in character['voice_actors']:
                if voice_actor['language'] not in language_whitelist:
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

    # Calculate person score
    for person in persons:
        person['score'] = 0

		# TODO use franchise instead of anime
        character_animes = set([
            anime['mal_id'] for character in person['characters'] for anime in character['animes']
        ])
        animes = set([anime['anime']['mal_id'] for anime in person['animes']])
        animes.update(character_animes)

        def score_anime(anime):
            if anime['mal_id'] not in animes:
                # Ignore anime if already counted as character
                return
            animes.remove(anime['mal_id'])

            # score = anim score ^ n / max score ^ n
            # n controls the importance of high scores
            n = 8
            person['score'] += anime['my_score'] ** n / 10 ** n

        # Score staff
        for anime in person['animes']:
            score_anime(anime['anime'])

        for character in person['characters']:
            for anime in character['animes']:
                score_anime(anime)

    # Sort person by score
    persons.sort(key=lambda person: person['score'], reverse=True)

    return persons

def print_staff(persons, show_top=10, min_works=2):
    # Only display person with more than X works
    persons = [person for person in persons if len(person['animes']) + len(person['characters']) >= min_works]

    for person in persons[:show_top]:
        showreel_url = f"https://www.youtube.com/results?search_query={quote(person['name'])}"
        print(f"\n{person['name']} ({person['works']} works, score: {person['score']:.2f}) - {showreel_url}")

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

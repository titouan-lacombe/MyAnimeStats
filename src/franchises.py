import unidecode, re

from .log import logger

log = logger.getChild(__name__)

def sanitize(text: str):
    # Unidecode
    text = unidecode.unidecode(text)
    # Lowercase
    text = text.lower()
    # Remove special characters
    text = re.sub(r"[^\w\s]", "", text)
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)
    # Remove leading and trailing spaces
    text = text.strip()
    return text

# Return the name of the franchise, none if not found
def get_franchise(a_title: str, f_title: str, auto: bool):
    words_a = a_title.split(" ")
    words_f = f_title.split(" ")
    min_w_len = min(len(words_a), len(words_f))

    # If in manual mode, just check if the manual title is in the anime title, else return None
    if not auto:
        match = re.search(f_title, a_title)
        log.debug(f"Franchise match (manual): {match is not None}")
        return f_title if match else None

    common = []
    for i in range(min_w_len):
        if sanitize(words_a[i]) == sanitize(words_f[i]):
            common.append(words_f[i])
        else:
            break
    franchise = " ".join(common)

    # If more than XX% of the characters of the shortest title are common, it is a franchise
    min_len = min(len(a_title), len(f_title))
    if len(franchise) / min_len > 0.8:
        log.debug(f"Franchise match (percent): {len(franchise)}/{min_len}")
        return franchise

    # If the length of the common string is more than X characters, it is a franchise
    if len(franchise) > 15:
        log.debug(f"Franchise match (length): {len(franchise)}")
        return franchise

    return None

# Return the name of the franchise, none if not found
def get_franchise_list(titles: list, auto: bool):
    if len(titles) == 0:
        return None

    log.debug(f"Franchise match: {', '.join(titles)}")

    franchise = titles[0]
    for title in titles[1:]:
        franchise = get_franchise(title, franchise, auto)

        if franchise is None:
            log.debug(f"Franchise match failed")
            return None

    log.debug(f"Franchise match success: '{franchise}'")
    return franchise
    
# Return the weighted mean of the given attribute
# If the attribute is None, it is ignored
def weighted_mean(animes, attr, wh_attr):
    total = 0
    weight = 0
    for anime in animes:
        if anime[attr] is None:
            continue
        if anime[wh_attr] is None:
            continue

        total += anime[attr] * anime[wh_attr]
        weight += anime[wh_attr]

    if weight <= 0:
        return None

    return total / weight

# Return the union of the given attribute
def union(animes, attr):
    return list(set(name['name'] for anime in animes for name in anime[attr]))

# Return the list of franchises from the given list of animes
# TODO add column franchise + group by
def get_franchises(animes: list):
    # List of known franchises (override the auto detection)
    known_franchises = [
        "Evangelion",
        "Code Geass",
        "Mushoku Tensei",
        "Fullmetal Alchemist: Brotherhood", # Separate from FMA 2003
        "Vinland Saga",
    ]

    # Initialize franchises list with known franchises
    franchises = []
    for franchise in known_franchises:
        franchises.append({
            "animes": [],
            "title": franchise,
            "auto": False,
        })

    # Build franchises list
    for anime in animes:
        match = None

        for i in range(len(franchises)):
            franchise = franchises[i]
            match = get_franchise(anime["title"], franchise["title"], franchise["auto"])

            # Found franchise: add anime to it
            if match:
                log.debug(f"Matched anime '{anime['title']}' to franchise '{match}'")
                franchises[i]["animes"].append(anime)
                franchises[i]["title"] = match
                break

        # Franchise not found: new franchise
        if not match:
            franchises.append({
                "animes": [anime],
                "title": anime["title"],
                "auto": True,
            })

    # for franchise in franchises:
    # 	titles = [anime["title"] for anime in franchise["animes"]]
    # 	log.debug(f"- {franchise['title']} [{', '.join(titles)}]")

    # Compute the aggregated data for each franchise
    franchises_aggr = []
    for franchise in franchises:
        animes = franchise['animes']

        if len(animes) == 0:
            continue

        # Set score to None if not scored (score == 0)
        for anime in animes:
            if anime['score'] == 0:
                anime['score'] = None
            if anime['my_score'] == 0:
                anime['my_score'] = None

        clean = {}
        clean['title'] = franchise['title']
        clean['title_english'] = get_franchise_list([
            anime["title_english"] or anime["title"] for anime in animes],
            True,
        )
        if clean['title_english'] is None:
            clean['title_english'] = clean['title']
        clean['episodes'] = sum(anime["episodes"] if anime["episodes"] is not None else 0 for anime in animes)
        clean['score'] = weighted_mean(animes, "score", 'episodes')
        clean['my_score'] = weighted_mean(animes, "my_score", 'episodes')
        clean['genres'] = union(animes, "genres")
        clean['themes'] = union(animes, "themes")
        clean['demographics'] = union(animes, "demographics")
        clean['studios'] = union(animes, "studios")
        clean['licensors'] = union(animes, "licensors")
        clean['producers'] = union(animes, "producers")

        franchises_aggr.append(clean)

    log.info(f"Found {len(franchises_aggr)} franchises")

    return franchises_aggr

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
    words1 = a_title.split(" ")
    words2 = f_title.split(" ")
    min_w_len = min(len(words1), len(words2))

    # If in manual mode, just check if the manual title is in the anime title, else return None
    if not auto:
        log.debug(f"Franchise match (manual): {f_title}")
        match = re.search(f_title, a_title)
        return f_title if match else None

    common = []
    for i in range(min_w_len):
        if sanitize(words1[i]) == sanitize(words2[i]):
            common.append(words1[i])
        else:
            break
    franchise = " ".join(common)

    # If more than XX% of the characters of the shortest title are common, it is a franchise
    min_len = min(len(a_title), len(f_title))
    if len(franchise) / min_len > 0.8:
        log.debug(f"Franchise match (XX%): {len(franchise)}/{min_len}")
        return franchise

    # If the length of the common string is more than X characters, it is a franchise
    if len(franchise) > 15:
        log.debug(f"Franchise match (X characters)")
        return franchise

    return None

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
def get_franchises(animes: list):
    # List of known franchises (override the auto detection)
    known_franchises = [
        "Evangelion",
        "Code Geass",
        "Mushoku Tensei",
        "Fullmetal Alchemist: Brotherhood", # Separate from FMA 2003
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

        # Set score to None if not scored (score == 0)
        for anime in animes:
            if anime['score'] == 0:
                anime['score'] = None
            if anime['my_score'] == 0:
                anime['my_score'] = None

        clean = {}
        clean['title'] = franchise['title']
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

import unidecode, re

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
		# print(f"Franchise match (manual): {f_title}")
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
		# print(f"Franchise match (XX%): {len(franchise)}/{min_len}")
		return franchise

	# If the length of the common string is more than X characters, it is a franchise
	if len(franchise) > 15:
		# print(f"Franchise match (X characters)")
		return franchise

	return None

# Return the weighted mean of the given attribute
def weighted_mean(animes, attr, total_episodes):
	if total_episodes > 0:  # Check to avoid division by zero
		return sum((anime[attr] if anime[attr] is not None else 0) * 
				   (anime["episodes"] if anime["episodes"] is not None else 0) 
				   for anime in animes) / total_episodes
	return None

# Return the union of the given attribute
def union(animes, attr):
	return list(set(name['name'] for anime in animes for name in anime[attr]))

# Return the list of franchises from the given list of animes
def get_franchises(animes: list):
	# Filter out the animes that aren't scored (to avoid messing up the weighted mean)
	# TODO if score = 0, don't count it in the weighted mean
	animes = [anime for anime in animes if anime['my_score'] != 0]

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
	# 	print(f"- {franchise['title']} [{', '.join(titles)}]")

	# Compute the aggregated data for each franchise
	franchises_aggr = []
	for franchise in franchises:
		animes = franchise['animes']

		clean = {}
		clean['title'] = franchise['title']
		clean['episodes'] = sum(anime["episodes"] if anime["episodes"] is not None else 0 for anime in animes)
		clean['score'] = weighted_mean(animes, "score", clean['episodes'])
		clean['my_score'] = weighted_mean(animes, "my_score", clean['episodes'])
		clean['genres'] = union(animes, "genres")
		clean['themes'] = union(animes, "themes")
		clean['demographics'] = union(animes, "demographics")
		clean['studios'] = union(animes, "studios")
		clean['licensors'] = union(animes, "licensors")
		clean['producers'] = union(animes, "producers")

		franchises_aggr.append(clean)
		
	print(f"Found {len(franchises_aggr)} franchises")

	return franchises_aggr

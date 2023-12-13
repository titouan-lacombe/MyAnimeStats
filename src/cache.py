import json, asyncio, pprint
from jikanpy import AioJikan
from pathlib import Path

JIKAN_SLEEP_TIME = 1.1

class Cache:
	def __init__(self, cache_dir: Path, get_data, is_expired=lambda _: False):
		self.cache_dir: Path = cache_dir
		self.get_data = get_data
		self.is_expired = is_expired

	async def get(self, id: int, *args, **kwargs):
		cache_file = self.cache_dir / f"{id}.json"

		if cache_file.exists():
			# print(f"Using cached data for {id}")
			cached = json.load(cache_file.open())
			if not self.is_expired(cached):
				return cached
		
		data, should_cache = await self.get_data(id, *args, **kwargs)
		if should_cache:
			# print(f"Caching data for {id}")
			cache_file.parent.mkdir(parents=True, exist_ok=True)
			json.dump(data, cache_file.open('w'))

		return data

async def rate_limit(coro, *args, **kwargs):
	data = await coro(*args, **kwargs)
	# print(f"Sleeping for {JIKAN_SLEEP_TIME} seconds")
	await asyncio.sleep(JIKAN_SLEEP_TIME) # Sleep to avoid rate limiting
	return data

class AnimeCache(Cache):
	def __init__(self, cache_dir: Path, jikan: AioJikan, extension=None):
		self.jikan = jikan
		self.extension = extension
		subdir = "anime" if self.extension is None else f"anime_{self.extension}"
		super().__init__(cache_dir / subdir, self.get_data)

	async def get_data(self, id=None, anime=None):
		# print(f"Getting data for anime {id} with extension {self.extension}")
		response = await rate_limit(self.jikan.anime, id, extension=self.extension)

		if anime is None:
			anime = response["data"]

		return response, anime['status'] == 'Finished Airing'

	async def get(self, id=None, anime=None):
		if id is None:
			id = anime["mal_id"]

		if id is None:
			raise ValueError("Either id or anime must be specified")

		response = await super().get(id, anime)
		return response["data"]

data = Path("data")
cache_dir = data / ".cache"
jikan_session = AioJikan()

anime_cache = AnimeCache(cache_dir, jikan_session)
character_cache = AnimeCache(cache_dir, jikan_session, extension="characters")
staff_cache = AnimeCache(cache_dir, jikan_session, extension="staff")

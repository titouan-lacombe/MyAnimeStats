import json, asyncio, os
from datetime import datetime
from jikanpy import AioJikan
from pathlib import Path

from src.log import logger

log = logger.getChild(__name__)

if os.getenv('SELF_HOST_JIKAN') != "true":
    JIKAN_URL, JIKAN_QPS = (None, 0.9)
else:
    JIKAN_PORT = os.getenv('JIKAN_PORT')
    if JIKAN_PORT is None:
        raise ValueError("JIKAN_PORT must be set when SELF_HOST_JIKAN is true")
    JIKAN_URL, JIKAN_QPS = (f"http://localhost:{JIKAN_PORT}/v4", 2)

# From https://stackoverflow.com/questions/38683243/asyncio-rate-limiting
from collections import deque
class RateLimitingSemaphore:
    def __init__(self, qps_limit, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.qps_limit = qps_limit

        # The number of calls that are queued up, waiting for their turn.
        self.queued_calls = 0

        # The times of the last N executions, where N=qps_limit - this should allow us to calculate the QPS within the
        # last ~ second. Note that this also allows us to schedule the first N executions immediately.
        self.call_times = deque()

    async def __aenter__(self):
        self.queued_calls += 1
        while True:
            cur_rate = 0
            if len(self.call_times) >= self.qps_limit:
                cur_rate = len(self.call_times) / (self.loop.time() - self.call_times[0])
            if cur_rate < self.qps_limit:
                break
            interval = 1. / self.qps_limit
            elapsed_time = self.loop.time() - self.call_times[-1]
            await asyncio.sleep(self.queued_calls * interval - elapsed_time)
        self.queued_calls -= 1

        if len(self.call_times) >= self.qps_limit:
            self.call_times.popleft()
        self.call_times.append(self.loop.time())

    async def __aexit__(self, exc_type, exc, tb):
        pass

class Cache:
    def __init__(self, cache_dir: Path, get_data, is_expired=lambda *args, **kwargs: False):
        self.cache_dir: Path = cache_dir
        self.get_data = get_data
        self.is_expired = is_expired

    async def get(self, id: int, *args, **kwargs):
        cache_file = self.cache_dir / f"{id}.json"

        if cache_file.exists():
            log.debug(f"Using cached data for {id}")
            cached = json.load(cache_file.open())
            if not self.is_expired(cached, *args, **kwargs):
                return cached

        data, should_cache = await self.get_data(id, *args, **kwargs)
        if should_cache:
            log.debug(f"Caching data for {id}")
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            json.dump(data, cache_file.open('w'))

        return data

class AnimeCache(Cache):
    def __init__(self, cache_dir: Path, jikan: AioJikan, extension=None):
        self.jikan = jikan
        self.extension = extension
        self.rate_limiter = RateLimitingSemaphore(JIKAN_QPS)
        subdir = "anime" if self.extension is None else f"anime_{self.extension}"
        super().__init__(cache_dir / subdir, self.get_data, self.is_expired)

    def is_expired(self, data, anime):
        if anime is None:
            anime = data["data"]

        if anime["status"] == "Finished Airing":
            return False

        # If younger than 24h
        date = datetime.strptime(data["headers"]["Date"], "%a, %d %b %Y %H:%M:%S %Z")
        if (datetime.now() - date).days == 0:
            return False

        return True

    async def get_data(self, id=None, anime=None):
        log.debug(f"Getting data for anime {id} with extension {self.extension}")

        retries = 0
        while True:
            try:
                async with self.rate_limiter:
                    response = await self.jikan.anime(id, extension=self.extension)
                break
            except Exception as e:
                retries += 1
                log.error(f"Error getting data for anime {id} with extension {self.extension}: {e}")
                if retries > 3:
                    raise e

                log.error(f"Retrying ({retries}/3)")
                await asyncio.sleep(5)

        if anime is None:
            anime = response["data"]

        return response, True

    async def get(self, id=None, anime=None):
        if id is None:
            id = anime["mal_id"]

        if id is None:
            raise ValueError("Either id or anime must be specified")

        response = await super().get(id, anime)
        return response["data"]

data = Path("data")
cache_dir = data / ".cache"
jikan_session = AioJikan(JIKAN_URL)

anime_cache = AnimeCache(cache_dir, jikan_session)
character_cache = AnimeCache(cache_dir, jikan_session, extension="characters")
staff_cache = AnimeCache(cache_dir, jikan_session, extension="staff")

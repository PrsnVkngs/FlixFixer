import asyncio
import atexit
import time
import aiohttp


class RateLimiter:
    def __init__(self, rate):
        self._rate = rate
        self._last_called = time.monotonic()

    async def wait(self):
        elapsed = time.monotonic() - self._last_called
        to_wait = 1 / self._rate - elapsed
        if to_wait > 0:
            await asyncio.sleep(to_wait)
        self._last_called = time.monotonic()


class TMDBClient:
    def __init__(self, rate_limiter):
        self.rate_limiter = rate_limiter
        self.session = aiohttp.ClientSession()

    async def get(self, url):
        await self.rate_limiter.wait()
        async with self.session.get(url) as response:
            return await response.json()

    async def close(self):
        await self.session.close()


class ConcurrentRequests:

    def __init__(self):
        self.rate_limiter = RateLimiter(rate=30)  # TMDB's rate limit is 30 req/sec
        self.client = TMDBClient(rate_limiter=self.rate_limiter)

    async def get_all_responses(self, urls: list):
        tasks = [self.client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return responses

    async def close(self):
        if not self.client.session.closed:
            await self.client.close()


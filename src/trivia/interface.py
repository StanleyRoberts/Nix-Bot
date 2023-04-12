import aiohttp
import re

from helpers.logger import Logger

logger = Logger()


class TriviaInterface:
    """Interface for managing a trivia connection

    Args:
        difficulty (int): Question difficulty

    """

    def __init__(self, difficulty: str = "4") -> None:
        self._cache = []
        self.difficulty = difficulty

    async def _fill_cache(self) -> None:
        """Refill trivia cache
        """
        async with aiohttp.ClientSession() as session:
            if self.difficulty == "random":
                api_url = 'http://jservice.io/api/clues?min_date=2000'
            else:
                api_url = 'http://jservice.io/api/clues?value={}&min_date=2000'.format(str(self.difficulty) + '00')
            async with session.get(api_url) as response:
                if response.ok:
                    def r(t): return re.sub('<[^<]+?>', '', t)  # strip HTML tags
                    self._cache = [(r(cjson['question']), r(cjson['answer']), r(cjson['category']['title']))
                                   for cjson in (await response.json(encoding="utf-8"))[:20]]
                    logger.debug("Successful cache refill")
                else:
                    logger.error("{0} Cache refill failed: {1}"
                                 .format(response.status, await response.content.read(-1)))

    async def get_trivia(self) -> tuple[str, str, str]:
        """Get a new triva question, its answer and the question category

        Returns:
            tuple[str, str, str]: question, answer, category
        """
        if not self._cache:
            logger.debug("refilling cache")
            await self._fill_cache()
        return self._cache.pop()

    @classmethod
    async def with_fill(cls, difficulty) -> 'TriviaInterface':
        self = cls(difficulty)
        await self._fill_cache()
        return self

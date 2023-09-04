import aiohttp
import re
from difflib import get_close_matches
from enum import Enum

from helpers.logger import Logger
from helpers.style import Emotes

logger = Logger()

MAX_POINTS = 5  # score required to win


class GuessValue(Enum):
    INCORRECT = 0
    CORRECT_NOT_WON = 1
    CORRECT_AND_WON = 2


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
                api_url = 'http://jservice.io/api/clues?min_date=2000-01-01'
            else:
                api_url = 'http://jservice.io/api/clues?value={}&min_date=2000-01-01'.format(
                    str(self.difficulty) + '00')
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
        if len(self._cache) == 0:
            logger.debug("refilling cache")
            await self._fill_cache()
        return self._cache.pop()

    @classmethod
    async def with_fill(cls, difficulty) -> 'TriviaInterface':
        self = cls(difficulty)
        await self._fill_cache()
        return self


class TriviaGame:
    """Manages a trivia game internal state

    Args:
        difficulty (int): Question difficulty

    """

    def __init__(self, player_id: int, difficulty: int):
        self._interface = TriviaInterface(difficulty)
        self.players = {player_id: 0}
        self.question, self.answer, self.category = None, None, None

    async def get_new_question(self) -> str:
        """Generates new question and returns it

        Returns:
            str: formatted string with the current question
        """
        self.question, self.answer, self.category = await self._interface.get_trivia()
        logger.debug(f"generated trivia, q: {self.question}, a: {self.answer}")
        return f"**New Question** {Emotes.SNEAKY}\nQuestion: {self.question}\nHint: {self.category}"

    def get_current_question(self) -> str:
        return f"**Current Question** {Emotes.SNEAKY}\nQuestion: {self.question}\nHint: {self.category}"

    def check_guess(self, content: str, id: int) -> bool:
        if content.isdigit() and content is self.answer or\
                get_close_matches(self.answer.lower(), [content.lower()], cutoff=0.8) != []:
            return self._handle_correct(id)
        else:
            return GuessValue.INCORRECT

    async def skip(self, id):
        if ((len(self.players) <= 1) or
                (id in self.players.keys())):
            old_answer = self.answer
            await self.get_new_question()
            return old_answer

    def _handle_correct(self, id):
        if id in self.players.keys():
            self.players[id] += 1
        else:
            self.players.update({id: 1})

        if self.players[id] >= MAX_POINTS:
            logger.debug("User has won", member_id=id)
            return GuessValue.CORRECT_AND_WON
        else:
            return GuessValue.CORRECT_NOT_WON

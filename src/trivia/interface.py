from difflib import get_close_matches
from enum import Enum
import requests
import json

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
        category (str): Question category

    """

    def __init__(self, category: str | None = None) -> None:
        self._cache: list[tuple[str, str] | None] = []
        self.category = category

    async def _fill_cache(self) -> None:
        """Refill trivia cache
        """
        api_url = 'https://the-trivia-api.com/v2/questions?difficulties=easy'
        if self.category:
            api_url += f'&categories={self.category}'

        response = requests.get(api_url, timeout=10)
        if response.status_code == requests.codes.ok:
            self._cache = [
                ((cjson['question']['text']), (cjson['correctAnswer']))
                for cjson in json.loads(response.text)
                if not any(
                    map(cjson['question']['text'].__contains__, ["these", "following"])
                )
            ]
            if not self._cache:
                logger.error(f"Response of Trivia API empty. url= {api_url}", )
                self._cache = [None]
            else:
                logger.debug("Successful cache refill")
        else:
            logger.error(f"{response.status_code} Cache refill failed: {response.text}")
            self._cache = [None]

    async def get_trivia(self) -> tuple[str, str] | None:
        """Get a new triva question, its answer and the question category

        Returns:
            tuple[str, str]: question, answer, category
        """
        if not self._cache:
            logger.debug("refilling cache")
            await self._fill_cache()
        return self._cache.pop()

    @classmethod
    async def with_fill(cls, difficulty: str) -> 'TriviaInterface':
        """Create and return a filled trivia interface

        Args:
            difficulty (str): Difficult question to fill cache with

        Returns:
            TriviaInterface: Created TriviaInterface
        """
        self = cls(difficulty)
        await self._fill_cache()
        return self


class TriviaGame:
    """Manages a trivia game internal state

    Args:
        category (str): Question category

    """

    def __init__(self, player_id: str, category: str | None):
        self._interface = TriviaInterface(category)
        self.players = {player_id: 0}
        self.question: str | None = None
        self.answer: str | None = None

    async def get_new_question(self) -> str | None:
        """Generates new question and returns it

        Returns:
            str: formatted string with the current question
        """

        self.question, self.answer = await self._interface.get_trivia() or (None, None)

        logger.debug(f"generated trivia, q: {self.question}, a: {self.answer}")
        if self.question:
            return f"**New Question** {Emotes.SNEAKY}\nQuestion: {self.question}\n"
        else:
            return None

    def get_current_question(self) -> str:
        """Get current question

        Returns:
            str: current question
        """
        return f"**Current Question** {Emotes.SNEAKY}\nQuestion: {self.question}\n"

    def check_guess(self, content: str, user_id: str) -> GuessValue:
        """Check if guess correct

        Args:
            content (str): User guess
            user_id (str): User id

        Returns:
            GuessValue: Whether guess was correct or not
        """
        if not self.answer:
            raise RuntimeError("Could not find answer")
        if content.isdigit() and content is self.answer or\
                get_close_matches(self.answer.lower(), [content.lower()], cutoff=0.8) != []:
            return self._handle_correct(user_id)
        else:
            return GuessValue.INCORRECT

    async def skip(self, user_id: str) -> str:
        """Skip question

        Args:
            user_id (str): User who initiated skip

        Returns:
            str: Answer for skipped question
        """
        if not self.answer:
            raise RuntimeError("Could not find answer")
        value: str = ""
        if ((len(self.players) <= 1) or
                (user_id in self.players)):
            old_answer = self.answer
            await self.get_new_question()
            value = old_answer
        return value

    def _handle_correct(self, user_id: str) -> GuessValue:
        if user_id in self.players:
            self.players[user_id] += 1
        else:
            self.players.update({user_id: 1})

        if self.players[user_id] >= MAX_POINTS:
            logger.debug("User has won", member_id=int(user_id))
            return GuessValue.CORRECT_AND_WON
        else:
            return GuessValue.CORRECT_NOT_WON

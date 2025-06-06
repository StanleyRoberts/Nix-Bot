import asyncpraw as praw  # type: ignore[import]
import asyncprawcore as prawcore  # type: ignore[import]
import random
import aiohttp
import io
import discord
import re

from helpers.style import Emotes
from helpers.env import CLIENT_ID, SECRET_KEY, USER_AGENT
from helpers.logger import Logger

logger = Logger()


class Post:
    """Class representing a reddit post

    Args:
        text (str): Reddit selfpost text, or link url
        url (str, optional): Link url. Defaults to None.
    """

    def __init__(self, text: str, url: str = "") -> None:
        self.text = text
        self._url = url
        self.img: list[discord.File] = []

    async def load_img(self) -> 'Post':
        """Load image from reddit post"""
        if self._url and re.search(r"\.(png|jpg|gif|jpeg)$", self._url):
            async with aiohttp.ClientSession() as session:
                async with session.get(self._url) as resp:
                    self.img = [discord.File(io.BytesIO(await resp.read()), self._url)]
        elif self._url:
            self.text += self._url
        return self


class RedditInterface:
    """Interface for managing a reddit connection

    Args:
        sub (str): Subreddit name
        time (str, optional): Time period to search in. Defaults to "day".

    """

    def __init__(self, sub: str, is_nsfw: bool = False, time: str = "day") -> None:
        self.cache: list[praw.models.reddit.submission.Submission] = []
        self._nsub = sub
        self.time = time
        self.is_nsfw = is_nsfw
        self.sub: str | None = None
        self.error_response: str | None = None

    @staticmethod
    async def valid_sub(subreddit: str) -> bool:
        """If the given sub is resolvable

        Args:
            subreddit (str): Subreddit name

        Returns:
            bool: returns True if the sub exists, and False otherwise
        """
        try:
            async with praw.Reddit(client_id=CLIENT_ID,
                                   client_secret=SECRET_KEY,
                                   user_agent=USER_AGENT) as interface:
                temp = await interface.subreddit(subreddit)
                [post async for post in temp.top("day", 1)]
            return True
        except prawcore.exceptions.AsyncPrawcoreException:
            return False

    @staticmethod
    async def single_post(subreddit: str, is_nsfw: bool, time: str) -> Post:
        """Returns a single post from a subreddit

        Args:
            subreddit (str): Subreddit name
            time (str): Time period to get post from

        Returns:
            Post: Top post found
        """
        reddit = RedditInterface(subreddit, is_nsfw, time)
        post = await reddit.get_post()
        return post

    async def set_subreddit(self, subreddit_name: str, num: int = 15) -> None:
        """Sets interface to point to new subreddit

        Using this also resets the number of cached reddit posts.

        Args:
            subreddit (str): Subreddit name
            num (int, optional): The number of reddit posts to cache. Defaults to 15.

        Returns:
            Post: _description_
        """
        if not self.sub == subreddit_name:
            try:
                async with praw.Reddit(client_id=CLIENT_ID,
                                       client_secret=SECRET_KEY,
                                       user_agent=USER_AGENT) as instance:
                    self.sub = subreddit_name
                    subreddit = await instance.subreddit(self.sub)
                    await subreddit.load()

                    if subreddit.over18 and not self.is_nsfw:
                        logger.warning(f"Subreddit {subreddit_name} is marked NSFW")
                        self.error_response = (
                            f"{Emotes.GOON} Subreddit '{subreddit_name}' is marked NSFW. "
                            f"This channel is not marked NSFW {Emotes.GOON}"
                        )
                        return

                    self.cache = [post async for post in subreddit.top(
                        time_filter=self.time, limit=num) if self.is_nsfw or not post.over_18]
                    logger.info(f"The subreddit {subreddit_name} was set for reddit.interface")
                    self.error_response = None

            except prawcore.exceptions.Redirect:
                logger.warning(f"Requested subreddit {subreddit_name} was not found")
                self.error_response = f"{Emotes.WTF} Subreddit '{subreddit_name}' not found"
            except prawcore.exceptions.NotFound:
                logger.warning(f"Requested subreddit {subreddit_name} is banned")
                self.error_response = f"{Emotes.WTF} Subreddit '{subreddit_name}' banned"
            except prawcore.exceptions.Forbidden:
                logger.warning(f"Requested subreddit {subreddit_name} is set to private")
                self.error_response = f"{Emotes.WTF} Subreddit '{subreddit_name}' private"
            except prawcore.AsyncPrawcoreException as e:
                logger.error(
                    f"Failure getting subreddit <{subreddit_name}>: {e.__class__.__name__}"
                )
                self.error_response = f"{Emotes.WTF} Unknown error, please try again later"

            random.shuffle(self.cache)

    async def get_post(self) -> Post:
        """Gets a random reddit post from the cache

        Returns:
            Post: Random reddit post
        Throws:
            IndexError: If cache is empty
        """

        if not self.sub:
            await self.set_subreddit(self._nsub)
        if self.error_response:
            logger.warning(f"Error while getting post: {self.error_response}")
            return Post(self.error_response)
        try:
            subm = self.cache.pop()
        except IndexError:
            logger.warning(f"The subreddit {self.sub} ran out of posts")
            return Post(f"Whoops, you ran out of posts! Try a different sub {Emotes.CONFUSED}")
        return await Post("**" + subm.title + "**\t*(r/" + subm.subreddit.display_name + ")*\n" +
                          (subm.selftext if subm.is_self else ""),
                          "" if subm.is_self else subm.url).load_img()

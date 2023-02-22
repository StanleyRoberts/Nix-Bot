import asyncpraw as praw
import asyncprawcore as prawcore
import random
import aiohttp
import io
import discord
import re

from helpers.style import Emotes
from helpers.env import CLIENT_ID, SECRET_KEY, USER_AGENT


class Post:
    """Class representing a reddit post

    Args:
        text (str): Reddit selfpost text, or link url
        url (str, optional): Link url. Defaults to None.
    """

    def __init__(self, text: str, url: str = None) -> None:
        self.text = text
        self._url = url
        self.img = []

    async def load_img(self) -> None:
        if self._url and re.search(r"\.(png|jpg|gif|jpeg)$", self._url):
            async with aiohttp.ClientSession() as session:
                async with session.get(self._url) as resp:
                    self.img = [discord.File(io.BytesIO(await resp.read()), self._url)]
        elif self._url:
            self.text = self._url
        return self


class RedditInterface:
    """Interface for managing a reddit connection

    Args:
        sub (str): Subreddit name
        time (str, optional): Time period to search in. Defaults to "day".

    """

    def __init__(self, sub: str, time: str = "day") -> None:
        self.reddit = praw.Reddit(client_id=CLIENT_ID,
                                  client_secret=SECRET_KEY,
                                  user_agent=USER_AGENT)
        self.cache = []
        self._nsub = sub
        self.time = time
        self.sub = None
        self.error_response = None

    @staticmethod
    async def valid_sub(subreddit: str) -> bool:
        """If the given sub is resolvable

        Args:
            subreddit (str): Subreddit name

        Returns:
            bool: returns True if the sub exists, and False otherwise
        """
        try:
            interface = RedditInterface(subreddit)
            temp = await interface.reddit.subreddit(subreddit)
            [post async for post in temp.top("day", 1)]
            return True
        except prawcore.exceptions.AsyncPrawcoreException:
            return False
        finally:
            await interface.reddit.close()

    @staticmethod
    async def single_post(subreddit: str, time: str) -> Post:
        """Returns a single post from a subreddit

        Args:
            subreddit (str): Subreddit name
            time (str): Time period to get post from

        Returns:
            Post: Top post found
        """
        reddit = RedditInterface(subreddit, time)
        post = await reddit.get_post()
        await reddit.reddit.close()
        return post

    async def set_subreddit(self, subreddit: str, num: int = 15) -> Post:
        """Sets interface to point to new subreddit

        Using this also resets the number of cached reddit posts.

        Args:
            subreddit (str): Subreddit name
            num (int, optional): The number of reddit posts to cache. Defaults to 15.

        Returns:
            Post: _description_
        """
        if not self.sub == subreddit:
            try:
                self.sub = await self.reddit.subreddit(subreddit)
                self.cache = [post async for post in self.sub.top(time_filter=self.time, limit=num)]
                self.error_response = None
            except prawcore.exceptions.Redirect:
                self.error_response = "{0} Subreddit \'{1}\' not found".format(Emotes.WTF, subreddit)
            except prawcore.exceptions.NotFound:
                self.error_response = "{0} Subreddit \'{1}\' banned".format(Emotes.WTF, subreddit)
            except prawcore.exceptions.Forbidden:
                self.error_response = "{0} Subreddit \'{1}\' private".format(Emotes.WTF, subreddit)

            random.shuffle(self.cache)
        return self.error_response is None

    async def get_post(self) -> Post:
        """Gets a random reddit post from the cache

        Returns:
            Post: Random reddit post
        Throws:
            IndexError: If cache is empty
        """
        if self.sub is None:
            self.sub = await self.set_subreddit(self._nsub)
        if self.error_response is not None:
            return Post(self.error_response)
        try:
            subm = self.cache.pop()
        except IndexError:
            return Post("Whoops, you ran out of posts! Try a different sub {0}".format(Emotes.CONFUSED))
        return await Post("**" + subm.title + "**\t*(r/" + subm.subreddit.display_name + ")*\n" +
                          (subm.selftext if subm.is_self else ""),
                          None if subm.is_self else subm.url).load_img()

    async def on_timeout(self) -> bool:
        self.reddit.close()
        return super().on_timeout()

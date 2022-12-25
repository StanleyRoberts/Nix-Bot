
from Nix import CLIENT_ID, SECRET_KEY, USER_AGENT
import asyncpraw as praw
import asyncprawcore as prawcore
from functions.style import Emotes
import random
import aiohttp
import io
import discord


class NewPost:
    def __init__(self, submission: praw.models.Submission):
        self._url = None if submission.is_self else submission.url
        self.resolvable = self._url is not None and \
            self._url[-4:] == ".jpg" or self._url[-4:] == ".png" or self._url[-4:] == ".gif"
        self.text = "**" + submission.title + \
            "**\t*(r/" + submission.subreddit.display_name + ")*\n" + \
            (submission.selftext if submission.is_self else (self._url if not self.resolvable else ""))
        self.img = []

    async def load_img(self):
        if self.resolvable:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._url) as resp:
                    self.img = [discord.File(io.BytesIO(await resp.read()), self._url)]


class ErrPost(NewPost):
    def __init__(self, err_msg: str):
        self.img = []
        self._url = None
        self.text = err_msg


class RedditInterface:
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=SECRET_KEY,
                         user_agent=USER_AGENT)

    @staticmethod
    async def valid_sub(subreddit: discord.Subreddit) -> bool:
        return not isinstance(await RedditInterface.get_post(subreddit, "all"), ErrPost)

    @staticmethod
    async def get_post(subreddit, time) -> NewPost:
        """
        Gets a random post (out of top 50) from a subreddit

        Args:
            subreddit (string): subreddit name to pull from
            time (string): time period to query (day, month, all, etc)

        Returns:
            string: reddit post, consisting of title and body in markdown format
        """
        response = "Unknown error searching for subreddit {0} {1}".format(Emotes.WTF, subreddit)
        try:
            subr = await RedditInterface.reddit.subreddit(subreddit)
            subm = random.choice([post async for post in subr.top(time_filter=time, limit=50)])
            post = NewPost(subm)
            await post.load_img()
            return post
        except prawcore.exceptions.Redirect:
            response = "{0} Subreddit \'".format(Emotes.WTF) + subreddit + "\' not found"
        except prawcore.exceptions.NotFound:
            response = "{0} Subreddit \'".format(Emotes.WTF) + subreddit + "\' banned"
        except prawcore.exceptions.Forbidden:
            response = "{0} Subreddit \'".format(Emotes.WTF) + subreddit + "\' private"
        return ErrPost(response)

import discord
import requests
import json
import asyncio
from difflib import get_close_matches

from discord.ext import commands
from helpers.env import NINJA_API_KEY
from helpers.logger import Logger
from helpers.style import Emotes
logger = Logger()


class Trivia(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='trivia', description="Start a game of Trivia")
    async def testing(self, ctx: discord.ApplicationContext,
                      category: discord.Option(str, default="general",
                                               choices=["artliterature", "language",
                                                        "sciencenature", "general",
                                                        "fooddrink", "peopleplaces",
                                                        "geography", "historyholidays",
                                                        "entertainment", "toysgames",
                                                        "music", "mathematics",
                                                        "religionmythology", "sportsleisure"])):
        embed = discord.Embed(title="You have started a game of Trivia")
        self.view = TriviaGame({ctx.user: 0}, category, ctx.channel)
        await ctx.respond(embed=embed, view=self.view)
        await self.view.send_question()

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg):
        if self.view is not None:
            await self.view.guessing(msg)


class TriviaGame(discord.ui.View):
    def __init__(self, players: dict[discord.User, int],
                 category: str, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.category = category
        self.players = players
        self.channel = channel
        self.lock = asyncio.Lock()
        self.question, self.answer = TriviaGame.get_trivia(category)

    async def send_question(self):
        await self.channel.send("Question: {}".format(self.question, Emotes.CONFUSED))

    async def guessing(self, msg: discord.Message):
        async with self.lock:
            logger.debug("Message was detected")
            if msg.channel.id == self.channel.id:
                logger.debug("Message detected during Trivia in Channel")
                if get_close_matches(self.answer, [msg.content]) != []:
                    logger.info("Correct answer in Trivia detected answer: {0}, msg: {1}"
                                .format(self.answer, msg.content))
                    if msg.author in self.players.keys():
                        self.players[msg.author] += 1
                    else:
                        self.players.update({msg.author: 1})
                    await msg.reply("This was the correct answer ({0}) {1}".format(self.answer, Emotes.BLEP))
                    self.question, self.answer = self.get_trivia(self.category)
                    await self.send_question()

    @staticmethod
    def get_trivia(category: str):
        """
        Takes a category and returns a question and the answer
        """
        api_url = 'https://api.api-ninjas.com/v1/trivia?category={}'.format(category)
        response = requests.get(api_url, headers={'X-Api-Key': NINJA_API_KEY})
        message = "Error: " + str(response.status_code) + "\n" + response.text
        cjson = json.loads(response.text)[0]
        if response.status_code == requests.codes.ok:
            logger.debug("Successful Trivia request")
            message = cjson['question'], cjson['answer']
        return message


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

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

    @commands.slash_command(name='trivia',
                            description="Start a game of Trivia where the first person to get 5 points wins")
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
        super().__init__(timeout=30)
        self.category = category
        self.players = players
        self.channel = channel
        self.question, self.answer = TriviaGame.get_trivia(self.category)
        self.lock = asyncio.Lock()
        self.on_timeout()

    async def send_question(self):
        self.question, self.answer = TriviaGame.get_trivia(self.category)
        self.message = await self.channel.send("Question: {}".format(self.question, Emotes.CONFUSED))
        await self.message.add_reaction(Emotes.CONFUSED)

    @commands.Cog.listener("on_raw_reaction_add")  # TODO make the on_reaction work
    async def skip(self, package: discord.RawReactionActionEvent):  # reaction: discord.Reaction, user: discord.User
        logger.debug("Reaction add detected")
        if package.message_id == self.message.id:
            if package.emoji == Emotes.CONFUSED and (len(self.players == 0) or package.member in self.players):
                await self.send_question()

    async def guessing(self, msg: discord.Message):
        """
        Checks if a guess is correct; Gives out a point and makes a new question if it is
        """
        async with self.lock:
            logger.debug("Message was detected")
            if msg.channel.id == self.channel.id:
                logger.debug("Message detected during Trivia in Channel")
                if msg.content.isdigit():
                    self.correct_answer(msg)
                elif get_close_matches(self.answer, [msg.content]) != []:
                    self.correct_answer(msg)

    async def correct_answer(self, msg: discord.Message):
        logger.info("Correct answer in Trivia detected answer: {0}, msg: {1}"
                    .format(self.answer, msg.content))
        if msg.author in self.players.keys():
            self.players[msg.author] += 1
        else:
            self.players.update({msg.author: 1})
        await msg.reply("This was the correct answer ({0}) {1}".format(self.answer, Emotes.BLEP))
        if self.players[msg.author] == 5:
            await self.channel.send("The winner of this game of Trivia is {}".format(msg.author.mention))
            self.timeout = 0
        else:
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
            print(cjson['answer'])
        return message


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

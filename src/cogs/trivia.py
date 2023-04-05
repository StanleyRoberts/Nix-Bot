import aiohttp
import discord
import asyncio
from difflib import get_close_matches
import re

from discord.ext import commands
from helpers.logger import Logger
from helpers.style import Emotes, string_to_emoji, Colours
logger = Logger()


class Trivia(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.aktive_views: list[TriviaGame] = []

    @commands.slash_command(name='trivia',
                            description="Start a game of Trivia where the first person to get 5 points wins")
    async def game_start(self, ctx: discord.ApplicationContext,
                         difficulty=discord.Option(str, default="random", required=False,
                                                   choices=["1", "2", "3", "4",
                                                            "5", "6", "8", "10"])):
        embed = discord.Embed(title="You have started a game of Trivia", colour=Colours.PRIMARY,
                              description="Difficulty: {}".format(difficulty))
        view = TriviaGame({ctx.user.id: 0}, ctx.channel, difficulty)

        def remove_view():
            logger.debug("View timeout detected")
            self.aktive_views.remove(view)
        view.on_timeout = remove_view
        self.aktive_views.append(view)
        await ctx.respond(embed=embed, view=view)
        await view.send_question()

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg: discord.Message):
        if len(self.aktive_views) > 0 and msg.author.id != self.bot.user.id:
            for view in self.aktive_views:
                await view.guessing(msg)

    @commands.Cog.listener("on_raw_reaction_add")
    async def skip(self, event: discord.RawReactionActionEvent):
        logger.debug("reaction_add detected", member_id=event.user_id)
        if len(self.aktive_views) > 0 and event.user_id != self.bot.user.id:
            for view in self.aktive_views:
                await view.skip_question(event)


class TriviaGame(discord.ui.View):
    """Is the View for and manages most of the Trivia game
            Args:
                players (dict[discord.User, int]): The discord users with atleast one point and their score
                channel (discord.TextChannel): The channel in which the trivia is being held
            """

    def __init__(self, players: dict[int, int], channel: discord.TextChannel, difficulty: str):
        super().__init__(timeout=300)
        self.players = players
        self.channel = channel
        self.lock = asyncio.Lock()
        self.trivias = []
        self.difficulty = difficulty

    async def send_question(self):
        """pops the trivia from the cache and sends it
            activates get_trivia if the cache is empty
        """
        if len(self.trivias) == 0:
            await self.get_trivia(self.difficulty)
        trivia = self.trivias.pop()
        self.question, self.answer, self.category = trivia
        logger.debug("Trivia question being send Question: {}, Answer: {}".format(self.question, self.answer))
        self.message = await self.channel.send("Hint: {} \nQuestion: {}".format(self.category, self.question))
        await self.message.add_reaction('⏩')

    async def skip_question(self, event: discord.RawReactionActionEvent):
        """skip the current question and show the answer
                Args:
                event (discord.RawReactionActionEvent) : Event of a user adding a reaction

        Skips if the emoji is used by a person in self.players or if noone has any points so far
        Sends out the answer of the question and the next question
        """
        logger.debug("Question skipped detected")
        if event.message_id == self.message.id:
            emoji = string_to_emoji('⏩')
            logger.debug("The players are: {} with the length of {}".format(
                self.players, len(self.players)))
            if event.emoji == emoji and (
                    (len(self.players) <= 1) or event.member.id in self.players.keys()):
                await self.channel.send("The answer was: {} {}".format(self.answer, Emotes.SUNGLASSES))
                await self.send_question()
                logger.debug("Question successfully skipped")
            else:
                logger.debug("Question skip failed")

    async def guessing(self, msg: discord.Message):
        """Checks if a guess is correct

        If the guess is a number it has to be exact, otherwise any (spellingwise) close guesses will count too
        """
        async with self.lock:
            logger.debug("Message was detected")
            if msg.channel.id == self.channel.id:
                logger.debug("Message detected during Trivia in Channel")
                if msg.content.isdigit() and msg.content is self.answer:
                    logger.debug("digit in trivia detected")
                    await self.correct_answer(msg)
                elif get_close_matches(self.answer, [msg.content]) != []:
                    await self.correct_answer(msg)
                else:
                    await msg.add_reaction(Emotes.BRUH)

    async def correct_answer(self, msg: discord.Message):
        """Manages the point for the user with the correct answer

            Takes the message of the correct answer; If the user is not in self.players
            it adds him with one point otherwise it checks if the user won, if not it gives him a point
        """
        logger.info("Correct answer in Trivia detected answer: {0}, msg: {1}"
                    .format(self.answer, msg.content))
        await msg.add_reaction(Emotes.WHOA)
        if msg.author.id in self.players.keys():
            logger.debug("User that is already in self.players has received another point")
            self.players[msg.author.id] += 1
        else:
            logger.debug("User is being added to self.players with one point")
            self.players.update({msg.author.id: 1})
        await msg.reply("This was the correct answer ({0}) {1}".format(self.answer, Emotes.HAPPY))
        if self.players[msg.author.id] >= 5:
            logger.debug("User has won")
            await self.channel.send("The winner of this game of Trivia is {} {}"
                                    .format(msg.author.mention, Emotes.TEEHEE))
            self.stop()
        else:
            logger.debug("The user hasnt won so the game goes on")
            await self.send_question()

    async def get_trivia(self, difficulty: str):
        """Takes a difficulty and returns a list of trivia questions

        Takes a difficulty and returns the question, answer, category,
        and difficulty of 100 trivia questions in a list of lists
        """
        async with aiohttp.ClientSession() as session:
            if difficulty == "random":
                api_url = 'http://jservice.io/api/clues?min_date=2000'
            else:
                api_url = 'http://jservice.io/api/clues?value={}&min_date=2000'.format(difficulty + '00')
                logger.debug(api_url)
            async with session.get(api_url) as response:
                if response.ok:
                    logger.debug("Successful Trivia request")
                    def r(t): return re.sub('<[^<]+?>', '', t)  # Takes out HTML tags
                    self.trivias = [(r(cjson['question']), r(cjson['answer']), r(cjson['category']['title']))
                                    for cjson in (await response.json(encoding="utf-8"))[:20]]
                else:
                    logger.error("Trivia request failed. Status: {} Error msg: {}"
                                 .format(response.status, await response.content.read(-1)))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

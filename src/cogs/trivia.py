import discord
import asyncio
from difflib import get_close_matches
import typing
from discord.ext import commands

from helpers.logger import Logger
from helpers.style import Emotes, string_to_emoji, Colours
from trivia.interface import TriviaInterface

logger = Logger()

SKIP = '⏩'  # emoji used for skip question
MAX_POINTS = 5  # score required to win


class Trivia(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.active_views: typing.Dict[int, TriviaGame] = {}

    @commands.slash_command(name='trivia',
                            description="Start a game of Trivia where the first person to get 5 points wins")
    async def game_start(self, ctx: discord.ApplicationContext,
                         difficulty=discord.Option(str, default="random", required=False,
                                                   choices=["1", "2", "3", "4",
                                                            "5", "6", "8", "10"])):
        if ctx.guild_id in self.active_views.keys():
            channel = self.active_views[ctx.guild_id].channel
            await ctx.respond(f"Uh oh! {Emotes.STARE} There is already an active trivia game in {channel.mention}")
            return
        view = TriviaGame({ctx.user.id: 0}, ctx.channel, difficulty)

        def remove_view():
            logger.debug("View timeout detected")
            try:
                self.active_views.pop(view.channel.guild.id)
            except KeyError:
                logger.error("tried to remove timed out view twice", guild_id=view.channel.guild.id)
        view.on_timeout = remove_view
        self.active_views.update({ctx.guild_id: view})
        await ctx.respond(embed=discord.Embed(title="You have started a game of Trivia", colour=Colours.PRIMARY,
                                              description=f"Difficulty: {difficulty}"), view=view)
        await view.start()

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg: discord.Message):
        if msg.author.id != self.bot.user.id and msg.guild.id in self.active_views.keys():
            await self.active_views[msg.guild.id].check_guess(msg)

    @commands.Cog.listener("on_reaction_add")
    async def skip(self, event: discord.RawReactionActionEvent):
        logger.debug("reaction_add detected", member_id=event.user_id)
        if event.user_id != self.bot.user.id and event.guild_id in self.active_views.keys():
            await self.active_views[event.guild_id].skip_question(event)


class TriviaGame(discord.ui.View):
    """View for the trivia game
            Args:
                players (dict[int, int]): the current players ids, mapped to their score
                channel (discord.TextChannel): The channel in which the trivia is being held
    """

    def __init__(self, players: dict[int, int], channel: discord.TextChannel, difficulty: str):
        super().__init__(timeout=300)
        self.players = players
        self.channel = channel
        self.lock = asyncio.Lock()
        self._interface = TriviaInterface(difficulty)
        self.message = None
        self.question, self.answer, self.category = None, None, None

    async def start(self):
        await self._send_question()

    async def _send_question(self):
        """Sends a new trivia question
        """
        self.question, self.answer, self.category = await self._interface.get_trivia()
        logger.debug(f"sending trivia, q: {self.question}, a: {self.answer}",
                     guild_id=self.channel.guild.id, channel_id=self.channel.id)
        self.message = await self.channel.send("Hint: {} \nQuestion: {}".format(self.category, self.question))
        await self.message.add_reaction(SKIP)

    async def skip_question(self, event: discord.RawReactionActionEvent):
        """Skips the current question if the event matches conditions

        Skips the current trivia question and displays the correct answer if the event message_id
        matches the most recent trivia message AND the event emoji matches the skip emoji.
        A user can only skip if there are fewer than 2 players, or they are in the game

                Args:
                event (discord.RawReactionActionEvent) : Event of a user adding a reaction

        """
        if event.message_id == self.message.id:
            logger.debug(f"question skipped, players: {self.players}",
                         guild_id=event.guild_id, channel_id=event.channel_id)
            if (event.emoji == string_to_emoji(SKIP)) and\
                ((len(self.players) <= 1) or
                 (event.member.id in self.players.keys())):
                await self.channel.send(f"The answer was: {self.answer} {Emotes.SUNGLASSES}")
                await self._send_question()
                logger.debug("Question successfully skipped",
                             guild_id=event.guild_id,
                             channel_id=event.channel_id)
            else:
                logger.debug("Question skip failed",
                             guild_id=event.guild_id,
                             channel_id=event.channel_id)

    async def check_guess(self, msg: discord.Message):
        """Checks if a guess is correct

        If the guess is a number it has to be exact, otherwise any (spellingwise) close guesses will count too
        """
        async with self.lock:
            if msg.channel.id == self.channel.id:
                logger.debug("trivia answer recieved",
                             guild_id=msg.guild.id, channel_id=msg.channel.id)
                if msg.content.isdigit() and msg.content is self.answer:
                    logger.debug("digit in trivia detected",
                                 guild_id=msg.guild.id, channel_id=msg.channel.id)
                    await self._handle_correct(msg)
                elif get_close_matches(self.answer.lower(), [msg.content.lower()]) != []:
                    await self._handle_correct(msg)
                else:
                    await msg.add_reaction(Emotes.BRUH)

    async def _handle_correct(self, msg: discord.Message):
        """Manages the point for the user with the correct answer

        On recieving a correct answer: increment the users points or,
        if they are not in the game, add them to the game with a single point
        """
        logger.info(f"Correct trivia answer {self.answer} (true={msg.content})",
                    guild_id=msg.guild.id, channel_id=msg.channel.id)
        await msg.add_reaction(Emotes.WHOA)
        if msg.author.id in self.players.keys():
            logger.debug("User that is already in self.players has received another point",
                         guild_id=msg.guild.id, channel_id=msg.channel.id)
            self.players[msg.author.id] += 1
        else:
            logger.debug("User is being added to self.players with one point",
                         guild_id=msg.guild.id, channel_id=msg.channel.id)
            self.players.update({msg.author.id: 1})
        await msg.reply("The correct answer was: '{0}' {1}".format(self.answer, Emotes.HAPPY))
        if self.players[msg.author.id] >= MAX_POINTS:
            logger.debug("User has won",
                         guild_id=msg.guild.id, channel_id=msg.channel.id)
            await self.channel.send(f"Congratulations! {msg.author.mention} has won with " +
                                    f"{MAX_POINTS} points! {Emotes.TEEHEE}")
            self.stop()
        else:
            await self._send_question()


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

import time
import discord
import asyncio
from difflib import get_close_matches
import typing
from discord.ext import commands

from helpers.logger import Logger
from helpers.style import Emotes, Colours
from trivia.interface import TriviaInterface

logger = Logger()

MAX_POINTS = 5  # score required to win


class Trivia(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.active_views: typing.Dict[int, TriviaGame] = {}

    @commands.slash_command(name='trivia',
                            description="Start a game of Trivia. The first person to get 5 points wins")
    async def game_start(self, ctx: discord.ApplicationContext,
                         difficulty=discord.Option(str, default="random", required=False,
                                                   choices=["1", "2", "3", "4",
                                                            "5", "6", "8", "10"])):
        if ctx.channel_id in self.active_views.keys():
            await ctx.respond(f"{Emotes.STARE} Uh oh! There is already an active trivia game in this channel")
            await ctx.respond(self.active_views[ctx.channel_id].get_current_question(),
                              view=self.active_views[ctx.channel_id])
            return

        interface = TriviaInterface(difficulty)

        def remove_view():
            logger.debug("TrivaGame view stopped")
            try:
                self.active_views.pop(view.message.channel.id)
            except KeyError:
                logger.error("tried to remove stopped view twice", guild_id=view.message.channel.id)

        view = TriviaGame({ctx.user.id: 0}, interface, remove_view)

        self.active_views.update({ctx.channel_id: view})
        await ctx.respond(embed=discord.Embed(title=f"{Emotes.UWU} You have started a game of Trivia",
                                              colour=Colours.PRIMARY, description=f"Difficulty: {difficulty}"))
        await ctx.send(await view.get_new_question(), view=view)

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg: discord.Message):
        if msg.author.id != self.bot.user.id and msg.channel.id in self.active_views.keys():
            await self.active_views[msg.channel.id].check_guess(msg)

    @commands.slash_command(name='stop_trivia', description='stops the in-progress trivia game in this channel')
    async def stop_trivia(self, ctx: discord.ApplicationContext):
        self.active_views[ctx.channel_id].on_timeout()


class TriviaGame(discord.ui.View):
    """View for the trivia game
            Args:
                players (dict[int, int]): the current players ids, mapped to their score
                difficulty (str): _description_
                interface (TriviaInterface): _description_
    """

    def __init__(self, players: dict[int, int], interface: TriviaInterface, callback):
        super().__init__(timeout=300)
        self.players = players
        self.lock = asyncio.Lock()
        self._interface = interface
        self.question, self.answer, self.category = None, None, None

        def timeout():
            callback()
            self.stop()
        self.on_timeout = timeout  # TODO timeout needs to be tested

    async def get_new_question(self) -> str:
        """Generates new question and returns it

        Returns:
            str: formatted string with the current question
        """
        self._new_question()
        return f"**New Question** {Emotes.SNEAKY}\nQuestion: {self.question}\nHint: {self.category}"

    def get_current_question(self) -> str:
        """Gets the current question

        Returns:
            str: formatted string with the current question
        """
        return f"**Current Question** {Emotes.SNEAKY}\nQuestion: {self.question}\nHint: {self.category}"

    async def _new_question(self):
        self.question, self.answer, self.category = await self._interface.get_trivia()
        logger.debug(f"generated trivia, q: {self.question}, a: {self.answer}")

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary,
                       emoji='⏩')
    async def change_sub_callback(self, _, interaction: discord.Interaction):
        logger.debug(f"question skipped, players: {self.players}",
                     guild_id=interaction.guild_id, channel_id=interaction.channel_id)
        if ((len(self.players) <= 1) or
                (interaction.user.id in self.players.keys())):
            await interaction.response.send_message(f"The answer was: {self.answer} {Emotes.SUNGLASSES}")
            await interaction.channel.send(await self.get_new_question(), view=self)
            logger.debug("Question successfully skipped",
                         guild_id=interaction.guild_id,
                         channel_id=interaction.channel_id)
        else:
            logger.debug("Question skip failed",
                         guild_id=interaction.guild_id,
                         channel_id=interaction.channel_id)

    async def check_guess(self, msg: discord.Message):
        """Checks if a guess is correct

        If the guess is a number it has to be exact, otherwise any (spellingwise) close guesses will count too
        """
        async with self.lock:
            if msg.channel.id == self.message.channel.id:
                logger.debug("trivia answer recieved",
                             guild_id=msg.guild.id, channel_id=msg.channel.id)
                if msg.content.isdigit() and msg.content is self.answer:
                    logger.debug("digit in trivia detected",
                                 guild_id=msg.guild.id, channel_id=msg.channel.id)
                    await self._handle_correct(msg)
                elif get_close_matches(self.answer.lower(), [msg.content.lower()], cutoff=0.8) != []:
                    await self._handle_correct(msg)
                else:
                    await msg.add_reaction(Emotes.BRUH)

    async def _handle_correct(self, msg: discord.Message):
        """Manages point assignments for correct answer

        On recieving a correct answer: increment the sending users points or,
        if they are not in the game, add them to the game with a single point.
        If user has won, display message and stop game.
        """
        logger.info(f"Correct trivia answer: {msg.content} (true={self.answer})",
                    guild_id=msg.guild.id, channel_id=msg.channel.id)
        await msg.add_reaction(Emotes.WHOA)
        if msg.author.id in self.players.keys():
            self.players[msg.author.id] += 1
        else:
            self.players.update({msg.author.id: 1})

        await msg.reply(f"You got the answer! ({self.answer}) " +
                        f"You are now at {self.players[msg.author.id]} points {Emotes.HAPPY}")

        if self.players[msg.author.id] >= MAX_POINTS:
            logger.debug("User has won",
                         guild_id=msg.guild.id, channel_id=msg.channel.id)
            await msg.reply(f"Congratulations! {msg.author.mention} has won with " +
                            f"{MAX_POINTS} points! {Emotes.TEEHEE}")
            self.on_timeout()
        else:
            await msg.channel.send(await self.get_new_question(), view=self)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

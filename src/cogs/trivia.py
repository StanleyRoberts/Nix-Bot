import discord
import typing
from discord.ext import commands

from helpers.logger import Logger
from helpers.style import Emotes, Colours

from trivia.interface import TriviaGame
from trivia.ui_kit import TriviaView

logger = Logger()

DIFFICULTY_DICT = {"very easy": "2", "easy": "4", "medium": "6",
                   "hard": "8", "very hard": "10", "all difficulties": "random"}


class Trivia(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.active_views: typing.Dict[int, TriviaView] = {}

    @commands.slash_command(name='trivia',
                            description="Start a game of Trivia. The first person to get 5 points wins")
    async def game_start(self, ctx: discord.ApplicationContext,
                         difficulty=discord.Option(str, default="all difficulties", required=False,
                                                   choices=DIFFICULTY_DICT.keys())):
        real_difficulty = DIFFICULTY_DICT[difficulty]
        if ctx.channel_id in self.active_views.keys():
            await ctx.respond(f"{Emotes.STARE} Uh oh! There is already an active trivia game in this channel")
            await ctx.respond(self.active_views[ctx.channel_id].get_current_question(),
                              view=self.active_views[ctx.channel_id])
            return

        game_state = TriviaGame(ctx.user.id, real_difficulty)

        def remove_view(channel_id: int):
            logger.debug("TrivaGame view stopped")
            try:
                self.active_views.pop(channel_id)
            except KeyError:
                logger.error("tried to remove stopped view twice", channel_id=channel_id)

        view = TriviaView(game_state, remove_view, ctx.channel_id)

        self.active_views.update({ctx.channel_id: view})
        await ctx.respond(embed=discord.Embed(title=f"{Emotes.UWU} You have started a game of Trivia",
                                              colour=Colours.PRIMARY, description=f"Difficulty: {difficulty}"))
        text = await view.get_question()
        if not text:
            await ctx.send(f"An error has acurred within the Trivia game {Emotes.CRYING}")
            await self.active_views[ctx.channel_id].on_timeout()
        else:
            await ctx.send(text, view=view)

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg: discord.Message):
        if msg.author.id != self.bot.user.id and msg.channel.id in self.active_views.keys():
            await self.active_views[msg.channel.id].handle_guess(msg)

    @commands.slash_command(name='stop_trivia', description='stops the in-progress trivia game in this channel')
    async def stop_trivia(self, ctx: discord.ApplicationContext):
        if not self.active_views[ctx.channel_id]:
            await ctx.respond(f"There is no Trivia active in this channel {Emotes.CONFUSED}")
        else:
            await ctx.respond(f"Trivia has been stopped by {ctx.user.mention} {Emotes.DRINKING}")
            await self.active_views[ctx.channel_id].on_timeout()


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

import discord
import typing
from discord.ext import commands

from helpers.logger import Logger
from helpers.style import Emotes, Colours

from trivia.interface import TriviaGame
from trivia.ui_kit import TriviaView

logger = Logger()


class Trivia(commands.Cog):

    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.active_views: typing.Dict[int, TriviaView] = {}

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

        game_state = TriviaGame(ctx.user.id, difficulty)

        def remove_view():
            logger.debug("TrivaGame view stopped")
            try:
                self.active_views.pop(view.message.channel.id)
            except KeyError:
                logger.error("tried to remove stopped view twice", guild_id=view.message.channel.id)

        view = TriviaView(game_state, remove_view)

        self.active_views.update({ctx.channel_id: view})
        await ctx.respond(embed=discord.Embed(title=f"{Emotes.UWU} You have started a game of Trivia",
                                              colour=Colours.PRIMARY, description=f"Difficulty: {difficulty}"))
        await ctx.send(await view.get_question(), view=view)

    @commands.Cog.listener("on_message")
    async def on_guess(self, msg: discord.Message):
        if isinstance(msg.channel, discord.abc.PrivateChannel):
            logger.info("on_guess activated in PrivateChannel", channel_id=msg.channel.id)
            return
        if self.bot.user is None:
            logger.error("Bot is offline")
            return
        if msg.author.id != self.bot.user.id and msg.channel.id in self.active_views.keys():
            await self.active_views[msg.channel.id].handle_guess(msg)

    @commands.slash_command(name='stop_trivia', description='stops the in-progress trivia game in this channel')
    async def stop_trivia(self, ctx: discord.ApplicationContext):
        await self.active_views[ctx.channel_id].on_timeout()


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Trivia(bot))

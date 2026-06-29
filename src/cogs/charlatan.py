from discord.ext import commands
import discord

from charlatan.interface import CharlatanGame
from charlatan.ui_kit import CharlatanLobby
from helpers.logger import Logger


logger = Logger()


class Charlatan(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext) -> None:
        logger.info("Starting Charlatan Game",
                    guild_id=ctx.guild_id if ctx.guild_id else -1,
                    channel_id=ctx.channel_id if ctx.channel_id else -1)
        game_state = CharlatanGame(ctx.author)
        await ctx.respond(embed=game_state.make_embed("Charlatan"),
                          view=CharlatanLobby(game_state))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))

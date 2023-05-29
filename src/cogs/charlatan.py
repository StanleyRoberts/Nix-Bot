# TODO this needs a lot of review before merge
# Ive put some todo comments around things I
# think might be issues.

from discord.ext import commands
import discord

from charlatan.interface import CharlatanGame
from charlatan.ui_kit import CharlatanLobby
import helpers.charlatan_helpers as helper
from helpers.logger import Logger


logger = Logger()


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        logger.info("Starting Charlatan Game", guild_id=ctx.guild_id, channel_id=ctx.channel_id)
        game_state = CharlatanGame({ctx.author: 0})
        await ctx.respond(embed=helper.make_embed(game_state.players, "Charlatan"),
                          view=CharlatanLobby(game_state))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))

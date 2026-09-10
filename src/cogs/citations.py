from discord.ext import commands
import discord

from citations.interface import CitationGame
from citations.ui_kit import CitationLobby
from helpers.logger import Logger


logger = Logger()


class MissingCitation(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='citations', description="Play a game of Citations")
    async def start_game(self, ctx: discord.ApplicationContext) -> None:
        logger.info("Starting Citations game",
                    guild_id=ctx.guild_id,
                    channel_id=ctx.channel_id)
        game_state = CitationGame(ctx.author)
        await ctx.respond(embed=game_state.make_lobby_embed("Citations"),
                          view=CitationLobby(game_state))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(MissingCitation(bot))

import discord
from discord.ext import commands

from helpers.logger import Logger
import helpers.database as db

logger = Logger()


class Debug(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='sql', description='log sql data')
    async def get_sql(self, ctx: discord.ApplicationContext, text: str) -> None:
        vals = db.select_from_unsafe(text)
        logger.info(vals)
        await ctx.respond("Check logs for output")

    @commands.slash_command(name='sync', description="Sync commands")
    async def sync(self, ctx: discord.ApplicationContext) -> None:
        await self.bot.sync_commands()
        await ctx.respond("Synced")

def setup(bot: discord.Bot) -> None:
    bot.add_cog(Debug(bot))

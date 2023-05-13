import discord
from discord.ext import commands

from helpers.logger import Logger
import helpers.database as db

logger = Logger()


class Debug(commands.Cog):
    @commands.slash_command(name='sql', description='log sql data')
    async def get_sql(self, _: discord.ApplicationContext, text: str):
        vals = db.select_from_unsafe(text)
        logger.info(vals)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Debug(bot))

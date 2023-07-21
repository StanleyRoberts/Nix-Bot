import discord
import requests
import json
from discord.ext import commands, tasks

import helpers.database as db
from helpers.style import Emotes, TIME
from helpers.env import NINJA_API_KEY
from helpers.logger import Logger

logger = Logger()


class HttpError(Exception):
    pass


class Facts(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_fact.start()

    @commands.slash_command(name='fact', description="Displays a random fact")
    async def send_fact(self, ctx: discord.ApplicationContext) -> None:
        try:
            fact = self.get_fact()
        except HttpError:
            logger.error("Couldnt get fact for slash command")
            return
        await ctx.respond(fact)
        logger.debug("Getting fact", member_id=ctx.user.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='set_fact_channel', description="Sets the channel for daily facts")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fact_channel(self, ctx: discord.ApplicationContext,
                               channel: discord.Option(discord.TextChannel, required=False)) -> None:
        if not channel:
            channel = ctx.channel
        db.single_SQL("UPDATE Guilds SET FactChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond(f"Facts channel set to {channel.mention} {Emotes.DRINKING}", ephemeral=True)
        logger.debug("Fact channel set", member_id=ctx.user.id, channel_id=channel.id)

    @commands.slash_command(name='stop_facts',
                            description="Disables daily facts (run set_fact_channel to enable again)")
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx: discord.ApplicationContext) -> None:
        db.single_SQL(
            "UPDATE Guilds SET FactChannelID=NULL WHERE ID=%s", (ctx.guild_id,))
        await ctx.respond(f"Stopping daily facts {Emotes.NOEMOTION}", ephemeral=True)
        logger.debug("Fact channel unset", member_id=ctx.user.id, guild_id=ctx.guild_id)

    @tasks.loop(time=TIME)
    async def daily_fact(self) -> None:
        """
        Called daily to print facts to fact channel
        """
        logger.info("Starting daily birthday loop")
        guilds = db.single_SQL("SELECT FactChannelID FROM Guilds")
        try:
            fact = self.get_fact()
        except HttpError:
            logger.error("Couldn't get fact for daily facts")
            return
        for factID in guilds:
            if factID[0]:
                logger.debug("Attempting to send fact message", channel_id=factID[0])
                logger.warning(f"Fact Cog: {self.__repr__()}")
                try:
                    await (await self.bot.fetch_channel(factID[0])).send("__Daily fact__\n" + fact)
                except discord.errors.Forbidden:
                    logger.info("Permission failure for sending fact message", channel_id=factID[0])
                    pass  # silently fail if no perms, TODO setup logging channel

    @staticmethod
    def get_fact() -> str:
        """
        Gets random fact from ninjas API

        Returns:
            string: Random fact
        """
        api_url = 'https://api.api-ninjas.com/v1/facts?limit=1'
        response = requests.get(api_url, headers={'X-Api-Key': NINJA_API_KEY})
        cjson = json.loads(response.text)
        if response.status_code == requests.codes.ok:
            return cjson[0]["fact"]
        else:
            err = f"Fact Error {response.status_code}: {cjson['message']}"
            logger.error(err)
            raise HttpError(err)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Facts(bot))

import discord
import requests
import json
from discord.ext import commands, tasks

import helpers.database as db
from helpers.style import Emotes, TIME, RESET
from helpers.env import NINJA_API_KEY
from helpers.logger import Logger

logger = Logger()


class Facts(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_fact.start()
        self.sent_today = False
        self.reset_fact.start()

    @commands.slash_command(name='fact', description="Displays a random fact")
    async def send_fact(self, ctx: discord.ApplicationContext) -> None:
        fact = self.get_fact()
        msg = (fact if fact else
               "Oh no, I can't think of any good facts right now." +
               f"Maybe I will think of one later{Emotes.CRYING}")
        await ctx.respond(msg)
        logger.debug("Getting fact", member_id=ctx.user.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='set_fact_channel', description="Sets the channel for daily facts")
    @discord.commands.option("channel", type=discord.TextChannel, required=False)
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fact_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel
    ) -> None:
        if not channel:
            channel = ctx.channel
        db.single_void_SQL("UPDATE Guilds SET FactChannelID=%s WHERE ID=%s",
                           (channel.id, ctx.guild_id))
        await ctx.respond(
            f"Facts channel set to {channel.mention} {Emotes.DRINKING}",
            ephemeral=True
        )
        logger.debug("Fact channel set", member_id=ctx.user.id, channel_id=channel.id)

    @commands.slash_command(
        name='stop_facts',
        description="Disables daily facts (run set_fact_channel to enable again)"
    )
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx: discord.ApplicationContext) -> None:
        db.single_void_SQL(
            "UPDATE Guilds SET FactChannelID=NULL WHERE ID=%s", (ctx.guild_id,))
        await ctx.respond(f"Stopping daily facts {Emotes.NOEMOTION}", ephemeral=True)
        logger.debug("Fact channel unset", member_id=ctx.user.id, guild_id=ctx.guild_id)

    @tasks.loop(time=RESET)
    async def reset_fact(self) -> None:
        self.sent_today = False

    @tasks.loop(time=TIME)
    async def daily_fact(self) -> None:
        """
        Called daily to print facts to fact channel
        """
        if self.sent_today:
            return
        self.sent_today = True
        logger.info("Starting daily fact loop")
        guilds = db.single_sql("SELECT FactChannelID FROM Guilds")
        fact = self.get_fact()
        for factID in guilds:
            if factID[0]:
                logger.debug("Attempting to send fact message", channel_id=factID[0])
                try:
                    msg = (("__Daily fact__\n" + fact) if fact else
                           "Oh no, I can't think of any good facts right now. " +
                           f"Maybe I will think of one later {Emotes.CRYING}")
                    channel = await self.bot.fetch_channel(factID[0])
                    if isinstance(channel, discord.abc.Messageable):
                        await channel.send(msg)
                    else:
                        logger.info("Channel for daily fact not messageable", channel_id=factID[0])
                except discord.errors.Forbidden:
                    logger.info("Permission failure for sending fact message", channel_id=factID[0])

    @staticmethod
    def get_fact() -> str | None:
        """
        Gets random fact from ninjas API

        Returns:
            string: Random fact or None if there was an error getting a fact
        """
        api_url = 'https://api.api-ninjas.com/v1/facts'
        if NINJA_API_KEY is None:
            logger.error("NINJA_API_KEY variable not available")
            return None
        response = requests.get(api_url, headers={'X-Api-Key': NINJA_API_KEY}, timeout=10)
        cjson = json.loads(response.text)
        if response.status_code == requests.codes.ok:
            return str(cjson[0]["fact"])
        else:
            logger.error(f"Fact Error {response.status_code}: {cjson}")
            return None


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Facts(bot))

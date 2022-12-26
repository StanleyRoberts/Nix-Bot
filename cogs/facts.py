import discord
import requests
import json
from discord.ext import commands, tasks

import functions.database as db
from functions.style import Emotes, TIME
from Nix import NINJA_API_KEY


class Facts(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_fact.start()

    @commands.slash_command(name='fact', description="Displays a random fact")
    async def send_fact(self, ctx: discord.ApplicationContext) -> None:
        await ctx.respond(self.get_fact())

    @commands.slash_command(name='set_fact_channel', description="Sets the channel for daily facts")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fact_channel(self, ctx: discord.ApplicationContext,
                               channel: discord.Option(discord.TextChannel, required=False)) -> None:
        if not channel:
            channel = ctx.channel
        db.single_SQL("UPDATE Guilds SET FactChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("Facts channel set to {0} {1}".format(channel.mention, Emotes.DRINKING), ephemeral=True)

    @commands.slash_command(name='stop_facts',
                            description="Disables daily facts (run set_fact_channel to enable again)")
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx: discord.ApplicationContext) -> None:
        db.single_SQL(
            "UPDATE Guilds SET FactChannelID=NULL WHERE ID=%s", (ctx.guild_id,))
        await ctx.respond("Stopping daily facts {0}".format(Emotes.NOEMOTION), ephemeral=True)

    @tasks.loop(time=TIME)
    async def daily_fact(self) -> None:
        """
        Called daily to print facts to fact channel
        """
        guilds = db.single_SQL("SELECT FactChannelID FROM Guilds")
        fact = self.get_fact()
        for factID in guilds:
            if factID[0]:
                try:
                    await (await self.bot.fetch_channel(factID[0])).send("__Daily fact__\n" + fact)
                except discord.errors.Forbidden:
                    pass  # silently fail if no perms, TODO setup logging channel

    @staticmethod
    def get_fact() -> str:
        """
        Gets random fact from ninjas API

        Returns:
            string: Random fact
        """
        api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
        response = requests.get(api_url, headers={'X-Api-Key': NINJA_API_KEY})
        message = "Error: " + str(response.status_code) + "\n" + response.text
        if response.status_code == requests.codes.ok:
            cjson = json.loads(response.text)
            message = cjson[0]["fact"]
        return message


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Facts(bot))

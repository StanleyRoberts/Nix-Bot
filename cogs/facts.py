import discord
import requests
import json
from discord.ext import commands, tasks

import functions.database as db
from functions.style import Emotes, Time
from Nix import API_KEY


class Facts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_fact.start()

    @commands.slash_command(name='fact', description="Displays a random fact")
    async def send_fact(self, ctx):
        await ctx.respond(self.get_fact())

    @commands.slash_command(name='set_fact_channel', description="Sets the channel for daily facts")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fact_channel(self, ctx, channel: discord.TextChannel):
        # TODO channel option should default to current context
        db.single_SQL("UPDATE Guilds SET FactChannelID=%s WHERE ID=%s",
                      (channel.id, ctx.guild_id))
        await ctx.respond("Facts channel set to {0} {1}"
                          .format(channel.mention, Emotes.DRINKING), ephemeral=True)

    @commands.slash_command(name='stop_facts',
                            description="Disables daily facts (run set_fact_channel to enable again)")
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx):
        db.single_SQL(
            "UPDATE Guilds SET FactChannelID=NULL WHERE ID=%s", (ctx.guild_id,))
        await ctx.respond("Stopping daily facts {0}".format(Emotes.NOEMOTION), ephemeral=True)

    @tasks.loop(time=TIME)
    async def daily_fact(self):
        """
        Called daily to print facts to fact channel
        """
        guilds = db.single_SQL("SELECT FactChannelID FROM Guilds")
        fact = self.get_fact()
        for factID in guilds:
            if factID[0]:
                await (await self.bot.fetch_channel(factID[0])).send(fact)

    @staticmethod
    def get_fact():
        """
        Gets random fact from ninjas API

        Returns:
            string: Random fact
        """
        api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
        response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
        message = "Error: " + str(response.status_code) + "\n" + response.text
        if response.status_code == requests.codes.ok:
            cjson = json.loads(response.text)
            message = cjson[0]["fact"]
        return message


def setup(bot):
    bot.add_cog(Facts(bot))

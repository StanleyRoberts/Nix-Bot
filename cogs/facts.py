import discord
from discord.ext import commands, tasks
import datetime as dt
import functions.database as db
import requests, json

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
        db.single_SQL("UPDATE Guilds SET FactChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:1026494037043187713> Facts channel set to {0}".format(channel.mention), ephemeral=True)

    @commands.slash_command(name='stop_facts', description="Disables daily facts (run set_fact_channel to enable again)")
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx):
        db.single_SQL("UPDATE Guilds SET FactChannelID=NULL WHERE ID=%s", (ctx.guild_id,))
        await ctx.respond("<:NixNoEmotion:1026494031670300773> Stopping daily facts", ephemeral=True)

    @tasks.loop(time=dt.time(hour=9))
    async def daily_fact(self):
        guilds = db.single_SQL("SELECT FactChannelID FROM Guilds")
        fact = self.get_fact()
        for factID in guilds:
            if factID[0]:
                await (await self.bot.fetch_channel(factID[0])).send(fact)
    
    @staticmethod
    def get_fact():
        api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
        response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
        message = "Error: "+str(response.status_code)+"\n"+response.text
        if response.status_code == requests.codes.ok:
            cjson = json.loads(response.text)
            message = cjson[0]["fact"]
        return message

def setup(bot):
    bot.add_cog(Facts(bot))
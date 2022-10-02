import discord
from discord.ext import commands
import functions.helpers as helper

class Facts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name='fact', description="Displays a random fact")
    async def send_fact(self, ctx):
        await ctx.respond(helper.get_fact())

    @commands.slash_command(name='set_fact_channel', description="Sets the channel for daily facts")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fact_channel(self, ctx, channel: discord.TextChannel):
        helper.single_SQL("UPDATE Guilds SET FactChannelID=? WHERE ID=?", (channel.id, ctx.guild_id))
        await ctx.respond("Facts channel set to {0}".format(channel))

    @commands.slash_command(name='stop_facts', description="Disables daily facts (run set_fact_channel to enable again)")
    @discord.commands.default_permissions(manage_guild=True)
    async def toggle_facts(self, ctx):
        helper.single_SQL("UPDATE Guilds SET FactChannelID=NULL WHERE ID=?", (ctx.guild_id,))
        await ctx.respond("Stopping daily facts")

def setup(bot):
    bot.add_cog(Facts(bot))
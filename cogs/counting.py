import discord
from discord.ext import commands
import functions.helpers as helper
import asyncio

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(helper.process_count(msg))
        #await helper.process_count(msg)
                    
    @commands.slash_command(name='set_fail_role', description="Sets the role the given to users who fail at counting")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_failRole(self, ctx, role: discord.Role):
        helper.single_SQL("UPDATE Guilds SET FailRoleID=%s WHERE ID=%s", (role.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:1026494037043187713> The fail role is set to {0}".format(role.mention), ephemeral=True)
        
    @commands.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx, channel: discord.TextChannel):   
        helper.single_SQL("UPDATE Guilds SET CountingChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:1026494037043187713> Counting channel set to {0}".format(channel.mention), ephemeral=True)

    @commands.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
    async def get_highscore(self, ctx):
        highscore = helper.single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = %s", (ctx.guild.id,))
        await ctx.respond("Your server highscore is {0}! <:NixWhoa:1026494032999895161>".format(highscore[0][0]))
        
    
def setup(bot):
    bot.add_cog(Counting(bot))
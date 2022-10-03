import discord
from discord.ext import commands
import functions.helpers as helper

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, msg):
        if(msg.content.isdigit()):
            values = helper.single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, "\
                                       "FailRoleID FROM Guilds WHERE ID=?", (msg.guild.id,))
            if(msg.channel.id == values[0][0]): #Checks for the right channel
                if(int(msg.content) != values[0][1] + 1): #Checks if it is the correct number
                    await helper.fail(msg, "Wrong number", values[0][4])
                elif(msg.author.id == values[0][2]): #Checks if the same user wrote twice 
                    await helper.fail(msg, "Same user entered two numbers", values[0][4])
                else:
                    await msg.add_reaction('<:NixBlep:1005522500811239466>') #!!Change for the NixP-Emote before adding it to the server!!
                    helper.single_SQL("UPDATE Guilds SET LastCounterID =?, CurrentCount = CurrentCount+1, HighScoreCounting="\
                                      "IIF(?>HighScoreCounting, ?, HighScoreCounting) WHERE ID =?",
                                      (msg.author.id, msg.content, msg.content, msg.guild.id))
                    
    @commands.slash_command(name='set_fail_role', description="Sets the role the given to users who fail at counting")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_failRole(self, ctx, role: discord.Role):
        helper.single_SQL("UPDATE Guilds SET FailRoleID=? WHERE ID=?", (role.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:929938768016863293> The fail role is set to {0}".format(role.mention), ephemeral=True)
        
    @commands.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx, channel: discord.TextChannel):   
        helper.single_SQL("UPDATE Guilds SET CountingChannelID=? WHERE ID=?", (channel.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:929938768016863293> Counting channel set to {0}".format(channel.mention), ephemeral=True)

    @commands.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
    async def get_highscore(self, ctx):
        highscore = helper.single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = ?", (ctx.guild.id,))
        await ctx.respond("Your server highscore is {0}! <:NixWhoa:930297260447785043>".format(highscore[0][0]))
        
    
def setup(bot):
    bot.add_cog(Counting(bot))
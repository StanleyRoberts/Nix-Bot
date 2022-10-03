import discord
from discord.ext import commands
import functions.helpers as helper

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(msg):
        if(msg.content.isdigit()):
            values = helper.single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, LoserRoleID FROM Guilds WHERE ID=?", (msg.guild.id,))
            if(msg.channel.id == values[0][0]): #Checks for the right channel
                if(int(msg.content) == values[0][1] + 1): #Checks if it is the correct number
                    if(msg.author.id != values[0][2]): #Checks if the same user wrote twice 
                        await msg.add_reaction('<:NixBlep:1025434663281492120>') #!!Change for the NixP-Emote before adding it to the server!!
                        helper.single_SQL("UPDATE Guilds SET LastCounterID =?, CurrentCount = CurrentCount+1 WHERE ID =?", (msg.author.id, msg.guild.id))
                        if(values[0][1] > values[0][3]):
                            helper.single_SQL("UPDATE Guilds SET HighScoreCounting =? WHERE ID =?", (values[0][1]+1, msg.guild.id))  
                            print(values[0][3])
                    else: #The same user wrote two times in a row
                        helper.API_KEYsingle_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID =?", (msg.guild.id,))
                        await msg.add_reaction('<:NixCrying:1025433818527715459>')
                        await msg.channel.send("Counting failed: same user entered two numbers in a row")
                        await msg.author.add_roles(msg.guild.get_role(values[0][4]))
                else: #Wrong number got typed in the chat
                    helper.single_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID = ?", (msg.guild.id,))
                    await msg.add_reaction('<:NixCrying:1025433818527715459>')
                    await msg.channel.send("Counting failed: Wrong number")
                    await msg.author.add_roles(msg.guild.get_role(values[0][4])) 
                    
    @commands.slash_command(name='set_loser_role', description="Set the role the person who failed at counting should get")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_loserRole(ctx, role: discord.Role):
        helper.single_SQL("UPDATE Guilds SET LoserRoleID=? WHERE ID=?", (role.id, ctx.guild_id))
        await ctx.respond("The role for the loser is set to {0}".format(role.name))
        
    @commands.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(ctx, channel: discord.TextChannel):   
        helper.single_SQL("UPDATE Guilds SET CountingChannelID=? WHERE ID=?", (channel.id, ctx.guild_id))
        await ctx.respond("Counting channel set to {0}".format(channel))

    @commands.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
    async def get_highscore(ctx):
        highscore = helper.single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = ?", (ctx.guild.id,))
        await ctx.respond("Your highscore is {0}".format(highscore[0][0]))
    
def setup(bot):
    bot.add_cog(Counting(bot))